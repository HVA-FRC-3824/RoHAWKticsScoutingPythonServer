import scipy.stats as stats
import math

from calculators.calculator import Calculator


class AllianceCalculator:
    '''Makes calculation about an teams

    Args:
        teams (list): list of :class:`Team` objects that make up the :class:`teams`
    '''
    def __init__(self, team_numbers):

        # Solves cyclical dependency
        from .team_calculator import TeamCalculator
        from database import Database

        self.database = Database()

        self.team_numbers = team_numbers
        self.team_calculators = []
        for team_number in self.team_numbers:
            self.team_calculators.append(TeamCalculator(team_number))

    def predicted_score(self, elimination=False):
        '''Predicted Score

        .. math::
            predicted\_score = \sum_{T \in A} sA(T) +
        '''
        p_score = 0
        auto_gears = 0
        teleop_gears = 0

        for team_number in self.team_numbers:
            team = self.database.get_team_calculated_data()
            p_score += (team.auto_shooting.high.made.average +
                        team.calc.auto_shooting.low.made.average / 3 +
                        team.calc.teleop_shooting.high.made.average / 3 +
                        team.calc.teleop_shooting.low.made.average / 9)
            # Add climbing points
            p_score += 50 * team.climb.success_percentage
            auto_gears += team.auto_gears.total.placed.average
            teleop_gears += team.teleop_gears.total.placed.average

        rotors = 0
        # Calculate points from gears
        if auto_gears >= 3:  # 2 rotors during auto
            p_score += 120
            rotors = 2
        elif auto_gears >= 1:  # 1 rotor during auto
            p_score += 60
            rotors = 1

        if auto_gears + teleop_gears >= 12:
            p_score += (4 - rotors) * 40
        elif auto_gears + teleop_gears >= 6:
            p_score += (3 - rotors) * 40
        elif auto_gears + teleop_gears >= 2:
            p_score += (2 - rotors) * 40
        else:
            p_score += (1 - rotors) * 40

        if elimination:
            p_score += self.rotor_chance() * 100
            p_score += self.pressure_chance() * 20

        return p_score

    def predicted_auto_score(self, elimination=False):
        p_auto_score = 0
        auto_gears = 0
        for team_number in self.team_numbers:
            team = self.database.get_team_calculated_data(team_number)
            p_auto_score += (team.auto_shooting.high.made.average + team.auto_shooting.low.made.average / 3)
            p_auto_score += (team.auto_baseline.average * 5)
            auto_gears += team.auto_gears.total.placed.average
        if auto_gears >= 3:
            p_auto_score += 120
        elif auto_gears >= 1:
            p_auto_score += 60
        return int(p_auto_score + 0.5)

    def std_predicted_score(self, elimination=False):
        '''Standard Deviation of Predicted Score

        .. math:: std\_predicted\_score = \sqrt{\sum_{T \in A} std\_auto\_ability(T)^2}
        '''
        std_p_score = 0.0

        p_auto_score = 0.0
        p_teleop_score = 0.0
        p_endgame_score = 0.0

        auto_gears = 0
        teleop_gears = 0

        for team_number in self.team_numbers:
            team = self.database.get_team_calculated_data(team_number)

            auto_gears += team.auto_gears.total.placed.average
            teleop_gears += team.teleop_gears.total.placed.average

            p_auto_score += team.auto_shooting.high.made.average
            p_auto_score += team.auto_shooting.low.made.average / 3
            p_teleop_score += team.teleop_shooting.high.made.average / 3
            p_teleop_score += team.teleop_shooting.low.made.average / 9
            p_endgame_score += team.climb.success_percentage * 50

        rotors = 0

        if auto_gears >= 3:
            p_auto_score += 120
            rotors = 2
        elif auto_gears >= 1:
            p_auto_score += 60
            rotors = 1

        if auto_gears + teleop_gears >= 12:
            p_teleop_score += (4 - rotors) * 40
        elif auto_gears + teleop_gears >= 6:
            p_teleop_score += (3 - rotors) * 40
        elif auto_gears + teleop_gears >= 2:
            p_teleop_score += (2 - rotors) * 40
        else:
            p_teleop_score += (1 - rotors) * 40

        std_p_score += p_auto_score ** 2
        std_p_score += p_teleop_score ** 2
        std_p_score += p_endgame_score ** 2

        std_p_score = math.sqrt(std_p_score)
        return std_p_score

    def win_probability_over(self, o):
        '''Win Probability

        In order to determine the win probability of teams A facing teams O, `Welch's
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

        In this case :math:`\\bar{X_1}` is the predicted score for teams A, :math:`s_1` is the standard
        deviation of the predicted score for teams A, and :math:`N_1` is the average number of
        completed matches for each of the team_calculators on teams A.

        win_chance(A,O) = T(t|v)

        t is the t-value generated by the Welch's test and v is the degrees of freedom
        approximated by the `Welch-Satterthwaite equation
        <https://en.wikipedia.org/wiki/WelchSatterthwaite_equation>`_

        .. math::
            v \\approx \\frac{(\\frac{s_1^2}{N_1}+\\frac{s_2^2}{N_2})^2}{\\frac{s_1^4}
            {N_1^2\\cdot v_1}+\\frac{s_2^4}{N_2^2\\cdot v_2}}

        where :math:`v_1 = N_1 - 1` (the degrees of freedom for the first variance) and :math:`v_2 = N_2 -1`
        '''
        if isinstance(o, list):
            return self.win_probability_over(AllianceCalculator(o))
        else:
            s_1 = self.std_predicted_score()
            s_2 = o.std_predicted_score()
            N_1 = self.sample_size()
            N_2 = o.sample_size()

            t = Calculator.welchs_test(self.predicted_score(), o.predicted_score(), s_1, s_2, N_1, N_2)

            v = Calculator.dof(s_1, s_2, N_1, N_2)
            win_chance = stats.t.cdf(t, v)
            return win_chance

    def sample_size(self):
        '''Returns the average number of completed matches for each of the team_calculators on teams A'''
        average = 0.0
        for team in self.team_calculators:
            average += team.num_completed_matches()
        average /= len(self.team_calculators)
        return average

    def pressure_chance(self):
        '''Returns the chance of the pressure reaching 40 kPa

        .. math::
            p = F(x | \mu, \sigma) = \\frac{1}{\sigma \sqrt{2 \pi}}
            \int_{- \infty}^x {e^{\\frac{-(t-\mu)^2}{2 \sigma^2}}} \, dt

        - x - threshold value which in this case is the kPa needed (40 kPa) represented by the teleop low goal value

        - :math:`\mu` - the mean of the sample which in this case is
            :math:`\sum_{T \in A} aH(T) * 9 + aL(T) * 3 + tH(T) * 3 + tL(T)`

        - :math:`\sigma` - the standard deviation of the sample which in this case is
            :math:`\sqrt{\sum_{T \in A} (aH(T) * 9)^2 + (aL(T) * 3)^2 + (tH(T) * 3)^2 +tL(T)^2}`

        Note:
            The internal unit in the function is the value of the teleop low goal (as that is the
            lowest value). This allows a combination of team_calculators to make up a point (e.g. team A does
            4 low goals and team B does 5).


        '''
        x = 40 * 9  # kPa in terms of low goal teleop
        auto_high = 0
        auto_low = 0
        teleop_high = 0
        teleop_low = 0
        auto_high_squared = 0
        auto_low_squared = 0
        teleop_high_squared = 0
        teleop_low_squared = 0
        for team_number in self.team_numbers:
            auto_high += t.auto_shooting.high.made.average * 9
            auto_high_squared += (t.auto_shooting.high.made.average * 9)**2
            auto_low += t.auto_shooting.low.made.average * 3
            auto_low_squared += (t.auto_shooting.low.made.average * 3)**2
            teleop_high += t.teleop_shooting.high.made.average * 3
            teleop_high_squared += (t.teleop_shooting.high.made.average * 3)**2
            teleop_low += t.teleop_shooting.low.made.average
            teleop_low_squared += (t.teleop_shooting.low.made.average)**2
        mu = auto_high + auto_low + teleop_high + teleop_low
        sigma = math.sqrt(auto_high_squared + auto_low_squared + teleop_high_squared + teleop_low_squared)
        return Calculator.probability_density(x, mu, sigma)

    def rotor_chance(self):
        '''Returns the chance of the 4 rotors being started

        .. math::
            p = F(x | \mu, \sigma) = \\frac{1}{\sigma \sqrt{2 \pi}}
            \int_{- \infty}^x {e^{\\frac{-(t-\mu)^2}{2 \sigma^2}}} \, dt

        - x - threshold value which in this case is the 12 gears needed

        - :math:`\mu` - the mean of the sample which in this case is
            :math:`\sum_{T \in A} aG(T) + \sum_{T \in A} tG(T)`

        - :math:`\sigma` - the standard deviation of the sample which in this case is
            :math:`\sqrt{\sum_{T \in A} aG(T)^2 + \sum_{T \in A} tG(T)^2}`
        '''
        x = 12  # gears
        mu = 0
        sigma = 0
        for team_number in self.team_numbers:
            mu += t.auto_gears.total.placed.average + t.teleop_gears.total.placed.average
            sigma += t.auto_gear.total.placed.average**2 + t.teleop_gears.total.placed.average**2
        sigma = math.sqrt(sigma)
        return Calculator.probability_density(x, mu, sigma)
