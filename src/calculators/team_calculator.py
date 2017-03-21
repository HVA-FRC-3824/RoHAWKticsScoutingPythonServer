from calculators.alliance_calculator import AllianceCalculator
from database import Database
from constants import Constants


class TeamCalculator:
    '''Makes all the higher level calculations for a specific team'''
    def __init__(self, team_number):
        self.team_number = team_number

    def num_completed_matches(self):
        '''Number of matches completed by this team'''
        return len(self.team.completed_matches)

    def first_pick_ability(self):
        '''Calculate the first pick ability which is the predicted offensive score that the
        team can contribute combined with our team.

        .. math:: first\_pick\_ability(X) = predicted_score(A)

        - predicted_score(A) predicted score of alliance A (this team and our team)
        '''
        if Constants.OUR_TEAM_NUMBER in Constants().team_numbers:
            alliance = [self.team_number, Constants.OUR_TEAM_NUMBER]
        else:
            alliance = [self.team_number]
        ac = AllianceCalculator(alliance)
        return ac.predicted_score()

    def second_pick_ability(self):
        '''Calculate the second pick ability

        .. math:: second\_pick\_ability(T) = (1 - dysfunctional\_percentage(T)) *
            (baseline_percentage(T) * 5 + climb_percentage(T) * 50)
        '''
        functional_percentage = (1 - self.dysfunctional_percentage())

        tcd = Database().get_team_calculated_data(self.team_number)
        average_baseline_points = tcd.auto_baseline.average * 5
        average_climb_points = tcd.climb.success_percentage * 50
        auto_gear_contribution = tcd.auto_gears.total.placed.average * 60

        # TODO: multipliers will be correctly determined later
        tqd = Database().get_team_qualitative_data(self.team_number)
        defense_contribution = tqd.defense.zscore * 1
        speed_contribution = tqd.speed.zscore * 1
        control_contribution = tqd.control.zscore * 1
        torque_contribution = tqd.torque.zscore * 1

        spa = functional_percentage * (average_baseline_points + auto_gear_contribution +
                                       defense_contribution + speed_contribution +
                                       control_contribution + torque_contribution +
                                       average_climb_points)
        return spa

    def third_pick_ability(self):
        '''Calculate the third pick ability'''
        tpa = 0.0
        return tpa

    def dysfunctional_percentage(self):
        '''Calculates the percentage of matches in which the robot was either
        not there or stopped moving
        '''
        tcd = Database().get_team_calculated_data(self.team_number)
        dysfunctional_matches = (tcd.dq.total + tcd.no_show.total
                                 + tcd.stopped_moving.total)
        logistics = Database().get_team_logistics(self.team_number)
        total_matches = len(logistics.match_numbers)
        return (dysfunctional_matches / total_matches)
