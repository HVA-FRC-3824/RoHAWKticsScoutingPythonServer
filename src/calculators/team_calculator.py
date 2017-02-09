from data_models.alliance import Alliance
from data_models.match import Match

from calculators.alliance_calculator import AllianceCalculator

from firebase_com import FirebaseCom
from constants import Constants


class TeamCalculator:
    '''Makes all the higher level calculations for a specific team'''
    def __init__(self, team):
        self.team = team
        self.firebase = FirebaseCom()

    def num_completed_matches(self):
        '''Number of matches completed by this team'''
        return len(self.team.completed_matches)

    def predicted_ranking_points(self):
        '''Predicts the number of ranking points at the end of qualifications using the actual
        ranking points from the completed matches and predicting ranking points acquired
        from the remaining ones.

        Note:
            Currently set up based on 2 for wins, 1 for ties, and 0 for loses. Additional
            RP will need to be added.

        Returns:
            predicted number of ranking points at the end of qualifications
        '''
        actual_RPs = 0
        for tmd in self.team.completed_matches.values():
            match = self.firebase.get_match(tmd.match_number)
            if match.is_blue(self.team.team_number):
                if match.scores[Match.BLUE] > match.scores[Match.RED]:
                    actual_RPs += 2
                elif match.scores[Match.BLUE] == match.scores[Match.RED]:
                    actual_RPs += 1
            else:
                if match.scores[Match.RED] > match.scores[Match.BLUE]:
                    actual_RPs += 2
                elif match.scores[Match.RED] == match.scores[Match.BLUE]:
                    actual_RPs += 1
        predicted_RPs = 0
        for match_index in range(len(self.team.completed_matches), len(self.team.info.match_numbers)):
            match = self.firebase.get_match(self.team.info.match_numbers[match_index])
            blue_alliance = Alliance(match.teams[0:2])
            red_alliance = Alliance(match.teams[3:5])

            if match.is_blue(self.team.team_number):
                ac = AllianceCalculator(blue_alliance, self.firebase)

                # Only predict wins not ties
                if ac.win_probability_over(red_alliance):
                    predicted_RPs += 2
            else:
                ac = AllianceCalculator(red_alliance, self.firebase)

                # Only predict wins not ties
                if ac.win_probability_over(blue_alliance):
                    predicted_RPs += 2
        return actual_RPs + predicted_RPs

    def first_pick_ability(self):
        '''Calculate the first pick ability which is the predicted offensive score that the
        team can contribute combined with our team.

        .. math:: first\_pick\_ability(X) = predicted_score(A)

        - predicted_score(A) predicted score of alliance A (this team and our team)
        '''
        alliance = Alliance(self.team, self.firebase.get_team(Constants.OUR_TEAM_NUMBER))
        ac = AllianceCalculator(alliance)
        return ac.predicted_score()

    def second_pick_ability(self):
        '''Calculate the second pick ability

        .. math:: second\_pick\_ability(T) = (1 - dysfunctional\_percentage(T)) * (baseline_percentage(T) * 5 + climb_percentage(T) * 50)
        '''
        functional_percentage = (1 - self.dysfunctional_percentage())
        average_baseline_points = self.team.calc.auto_baseline.average() * 5
        average_climb_points = self.team.calc.endgame_climb_successful.average * 50
        auto_gear_contribution = self.team.calc.auto_total_gears_placed.average * 60
        if auto_gear_contribution > 40:
            teleop_gear_contribution = self.team.calc.teleop_total_gears_placed.average * 260 / 11
        else:
            teleop_gear_contribution = self.team.calc.teleop_total_gears_placed.average * 220 / 12
        gear_contribution = auto_gear_contribution + teleop_gear_contribution

        # multipliers will be correctly determined later
        defense_contribution = self.team.calc.zscore_control * 4
        speed_contribution = self.team.calc.zscore_speed * 2
        control_contribution = self.team.calc.zscore_control * 4

        spa =  functional_percentage * (average_baseline_points + gear_contribution +
                                        defense_contribution + speed_contribution +
                                        control_contribution + average_climb_points)
        return spa

    def third_pick_ability(self):
        '''Calculate the third pick ability'''
        tpa = 0.0
        return tpa

    def dysfunctional_percentage(self):
        '''Calculates the percentage of matches in which the robot was either
        not there or stopped moving
        '''
        dysfunctional_matches = (self.team.calc.dq.total + self.team.calc.no_show.total
                                 + self.team.calc.stopped_moving.total)
        total_matches = len(self.team.info.match_numbers)
        return (dysfunctional_matches / total_matches)
