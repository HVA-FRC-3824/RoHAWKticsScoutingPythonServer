from data_models.alliance import Alliance
from data_models.match import Match

from calculators.alliance_calculation import AllianceCalculation

from constants import Constants


class TeamCalculation:
    def __init__(self, team, firebase):
        self.team = team
        self.firebase = firebase

    def auto_ability(self):
        return 0.0

    def std_auto_ability(self):
        return 0.0

    def num_completed_matches(self):
        return len(self.team.completed_matches)

    def predicted_ranking_points(self):
        '''
            Predicts the number of ranking points at the end of qualifications using the actual
            ranking points from the completed matches and predicting ranking points acquired
            from the remaining ones.

            Note:
            Currently set up based on 2 for wins, 1 for ties, and 0 for loses. Additional
            RP will need to be added.

            :return predicted number of ranking points at the end of qualifications
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
                ac = AllianceCalculation(blue_alliance, self.firebase)

                # Only predict wins not ties
                if ac.win_probability_over(red_alliance):
                    predicted_RPs += 2
            else:
                ac = AllianceCalculation(red_alliance, self.firebase)

                # Only predict wins not ties
                if ac.win_probability_over(blue_alliance):
                    predicted_RPs += 2
        return actual_RPs + predicted_RPs

    def predict_first_tie_breaker(self):
        '''
            Predict the first tie breaker for rankings. Use the actual value for matches that
            are completed and predict the value for ones that are not.
        '''
        return 0.0

    def predict_second_tie_breaker(self):
        '''
            Predict the second tie breaker for rankings. Use the actual value for matches that
            are completed and predict the values for ones that are not.
        '''
        return 0.0

    def first_pick_ability(self):
        '''
            Calculate the first pick ability which is the predicted offensive score that the
            team can contribute combined with our team.

            fpa(X) = S_p(A)

            - S_p(A) predicted score of alliance A (this team and our team)
        '''
        fpa = 0.0
        alliance = Alliance(self.team, self.firebase.get_team(Constants.OUR_TEAM_NUMBER))
        ac = AllianceCalculation(alliance)
        fpa += ac.predicted_score()
        return fpa

    def second_pick_ability(self):
        '''
            Calculate the second pick ability

            spa(T) = [1 - dfp(T)] * [aA(T)]
        '''
        spa = 0.0
        spa += self.auto_ability()
        spa *= self.dysfunctional_percentage()
        return spa

    def third_pick_ability(self):
        tpa = 0.0
        return tpa

    def dysfunctional_percentage(self):
        dysfunctional_matches = (self.team.calc.dq.total + self.team.calc.no_show.total
                                 + self.team.calc.stopped_moving.total)
        total_matches = len(self.team.info.match_numbers)
        return (dysfunctional_matches / total_matches)
