from .data_model import DataModel


class Match(DataModel):
    BLUE = 0
    RED = 1

    def __init__(self):
        self.match_number = -1
        self.teams = []
        self.scores = []

    def is_blue(self, team_number):
        return True if team_number in self.teams[0:2] else False

    def is_red(self, team_number):
        return not self.is_blue(team_number)
