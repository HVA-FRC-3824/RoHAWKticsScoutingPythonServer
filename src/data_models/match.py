from .data_model import DataModel
from calculators.alliance_calculator import AllianceCalculator


class Match(DataModel):
    '''Data model that represents a match'''
    BLUE = 0
    RED = 1

    def __init__(self, d=None):
        DataModel.__init__(self)

        self.match_number = -1
        self.team_numbers = []
        self.predicted_scores = []
        self.predicted_auto = []  # for second tie breaker
        self.predicted_kpa_rp = []
        self.predicted_rotor_rp = []

        self.score_breakdown = None

        if d is not None:
            self.set(d)

    def is_blue(self, team_number):
        '''Returns whether the team is on the blue alliance in this match'''
        return True if team_number in self.team_numbers[0:2] else False

    def is_red(self, team_number):
        '''Returns whether the team is on the red alliance in this match'''
        return not self.is_blue(team_number)

    def update_prediction(self):
        blue = AllianceCalculator(self.team_numbers[0:2])
        red = AllianceCalculator(self.team_numbers[3:5])

        self.predicted_scores = [blue.predicted_score(), red.predicted_score()]
        self.predicted_auto = [blue.predicted_auto_score(), red.predicted_auto_score()]
        self.predicted_kpa_rp = [blue.pressure_chance() > 0.5, red.pressure_chance() > 0.5]
        self.predicted_rotor_rp = [blue.rotor_chance() > 0.5, red.rotor_chance() > 0.5]
