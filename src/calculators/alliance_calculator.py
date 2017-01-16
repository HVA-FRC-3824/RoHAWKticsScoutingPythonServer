import scipy.stats as stats
import math

from data_models.alliance import Alliance
from firebase_com import FirebaseCom
from calculators.calculator import Calculator


class AllianceCalculator:
    '''Makes calculation about an alliance

    Args:
        alliance (list): list of :class:`Team` objects that make up the :class:`alliance`
    '''
    def __init__(self, alliance):

        # Solves cyclical dependency
        from .team_calculation import TeamCalculator

        self.alliance = alliance
        self.teams = []
        for team in self.alliance.teams:
            self.teams.append(TeamCalculator(team))
        self.firebase = FirebaseCom()

    def predicted_score(self, elimination=False):
        '''Predicted Score

        .. math::
            predicted\_score = \sum_{T \in A} sA(T) +
        '''
        p_score = 0
        auto_gears = 0
        teleop_gears = 0

        for team in self.teams:
            p_score += (team.calc.auto_high_goal_made.average +
                        team.calc.auto_low_goal_made / 3 +
                        team.calc.teleop_high_goal_made.average / 3 +
                        team.calc.teleop_low_goal_made.average / 9)
            # Add climbing points
            p_score += 50 * team.calc.climb.average
            auto_gears += team.calc.auto_gears_delivered.average
            teleop_gears += team.calc.teleop_gears_delivered.average

        # Calculate points from gears
        if auto_gears >= 3:  # 2 rotors during auto
            p_score += 120
            if teleop_gears >= 9:  # 2 rotors during teleop
                p_score += 80
            elif teleop_gears >= 3:  # 1 rotor during teleop
                p_score += 40
        elif auto_gears >= 1:  # 1 rotor during auto
            p_score += 60
            if teleop_gears + auto_gears >= 12:  # 3 rotors during teleop
                p_score += 120
            elif teleop_gears + auto_gears >= 6:  # 2 rotors during teleop
                p_score += 80
            elif teleop_gears + auto_gears >= 2:  # 1 rotor during teleop
                p_score += 40
        else:
            if teleop_gears >= 12:  # 4 rotors
                p_score += 160
            elif teleop_gears >= 6:  # 3 rotors
                p_score += 120
            elif teleop_gears >= 2:  # 2 rotors
                p_score += 80
            else:  # Reserve Gear
                p_score += 40

        if elimination:
            p_score += self.rotor_chance() * 100
            p_score += self.pressure_chance() * 20

        return p_score

    def std_predicted_score(self, elimination=False):
        '''Standard Deviation of Predicted Score

        .. math:: std\_predicted\_score = \sqrt{\sum_{T \in A} std\_auto\_ability(T)^2}
        '''
        std_p_score = 0.0
        for team in self.teams:
            std_p_score += team.std_auto_ability() ** 2
        std_p_score = std_p_score ** 0.5
        return std_p_score

    def win_probability_over(self, o):
        '''Win Probability

        In order to determine the win probability of alliance A facing alliance O, `Welch's
        t-test <https://en.wikipedia.org/wiki/Welch%27s_t-test>`_. This test is expressed
        using the formula

        .. math:: t = \\frac{ \\bar{X_1} + \\bar{X_2} }{ \sqrt{ \\frac{ s_1^2 }{ N_1 } + \\frac{ s_2^2 }{ N_2 } } }

        - :math:`\\bar{X_1}` is the mean of the first sample
        - :math:`s_1` is the standard deviation of the first sample
        - :math:`N_1` is the size of the first sample

        - :math:`\\bar{X_2}` is the mean of the second sample
        - :math:`s_2` is the standard deviation of the second sample
        - :math:`N_2` is the size of the second sample

        This t is then converted to a win probability using the `cumulative distribution
        function <https://en.wikipedia.org/wiki/Cumulative_distribution_function>`_ for a
        t-distribution T(t|v).

        In this case :math:`\\bar{X_1}` is the predicted score for alliance A, :math:`s_1` is the standard
        deviation of the predicted score for alliance A, and :math:`N_1` is the average number of
        completed matches for each of the teams on alliance A.

        win_chance(A,O) = T(t|v)

        t is the t-value generated by the Welch's test and v is the degrees of freedom
        approximated by the `Welch-Satterthwaite equation
        <https://en.wikipedia.org/wiki/WelchSatterthwaite_equation>`_

        .. math::
            v \\approx \\frac{(\\frac{s_1^2}{N_1}+\\frac{s_2^2}{N_2})^2}{\\frac{s_1^4}
            {N_1^2\\cdot v_1}+\\frac{s_2^4}{N_2^2\\cdot v_2}}

        where :math:`v_1 = N_1 - 1` (the degrees of freedom for the first variance) and :math:`v_2 = N_2 -1`
        '''
        if isinstance(o, Alliance):
            return self.win_probability_over(AllianceCalculator(o))
        else:
            s_1 = self.std_predicted_score()
            s_2 = o.std_predicted_score()
            N_1 = self.sample_size()
            N_2 = o.sample_size()

            t = Calculator.welchs_test(self.predicted_score, o.predicted_score(), s_1, s_2, N_1, N_2)

            v = Calculator.dof(s_1, s_2, N_1, N_2)
            win_chance = stats.t.cdf(t, v)
            return win_chance

    def sample_size(self):
        '''Returns the average number of completed matches for each of the teams on alliance A'''
        average = 0.0
        for team in self.teams:
            average += team.num_completed_matches()
        average /= len(self.teams)
        return average

    def pressure_chance(self):
        '''Returns the chance of the pressure reaching 40 kPa

        .. math::
            p = F(x | \mu, \sigma) = \\frac{1}{\sigma \sqrt{2 \pi}} \int_{- \infty}^x {e^{\\frac{-(t-\mu)^2}{2 \sigma^2}}} \, dt

        - x - threshold value which in this case is the kPa needed (40 kPa) represented by the teleop low goal value

        - :math:`\mu` - the mean of the sample which in this case is
            :math:`\sum_{T \in A} aH(T) * 9 + aL(T) * 3 + tH(T) * 3 + tL(T)`

        - :math:`\sigma` - the standard deviation of the sample which in this case is
            :math:`\sqrt{\sum_{T \in A} (aH(T) * 9)^2 + (aL(T) * 3)^2 + (tH(T) * 3)^2 +tL(T)^2}`

        Note:
            The internal unit in the function is the value of the teleop low goal (as that is the
            lowest value). This allows a combination of teams to make up a point (e.g. team A does
            4 low goals and team B does 5).


        '''
        x = 40 * 9  # kPa
        auto_high = 0
        auto_low = 0
        teleop_high = 0
        teleop_low = 0
        auto_high_squared = 0
        auto_low_squared = 0
        teleop_high_squared = 0
        teleop_low_squared = 0
        for t in self.teams:
            auto_high += t.calc.auto_high_goal_made.average * 9
            auto_high_squared += (t.calc.auto_high_goal_made.average * 9)**2
            auto_low += t.calc.auto_low_goal_made.average * 3
            auto_low_squared += (t.calc.auto_low_goal_made.average * 3)**2
            teleop_high += t.calc.teleop_high_goal_made.average * 3
            teleop_high_squared += (t.calc.teleop_high_goal_made.average * 3)**2
            teleop_low += t.calc.teleop_low_goal_made.average
            teleop_low_squared += (t.calc.teleop_low_goal_made.average)**2
        mu = auto_high + auto_low + teleop_high + teleop_low
        sigma = math.sqrt(auto_high_squared + auto_low_squared + teleop_high_squared + teleop_low_squared)
        return Calculator.probability_density(x, mu, sigma)

    def rotor_chance(self):
        '''Returns the chance of the 4 rotors being started

        .. math::
            p = F(x | \mu, \sigma) = \\frac{1}{\sigma \sqrt{2 \pi}} \int_{- \infty}^x {e^{\\frac{-(t-\mu)^2}{2 \sigma^2}}} \, dt

        - x - threshold value which in this case is the 12 gears needed

        - :math:`\mu` - the mean of the sample which in this case is
            :math:`\sum_{T \in A} aG(T) + \sum_{T \in A} tG(T)`

        - :math:`\sigma` - the standard deviation of the sample which in this case is
            :math:`\sqrt{\sum_{T \in A} aG(T)^2 + \sum_{T \in A} tG(T)^2}`
        '''
        x = 12  # gears
        mu = 0
        sigma = 0
        for t in self.teams:
            mu += t.calc.auto_gears_delivered.average + t.calc.teleop_gears_delivered.average
            sigma += t.calc.gears_delivered.average**2 + t.calc.teleop_gears_delivered.average**2
        sigma = math.sqrt(sigma)
        return Calculator.probability_density(x, mu, sigma)