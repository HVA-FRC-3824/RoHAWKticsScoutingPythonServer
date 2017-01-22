from .data_model import DataModel


class Match(DataModel):
    '''Data model that represents a match'''
    BLUE = 0
    RED = 1

    def __init__(self, **kwargs):
        self.match_number = -1
        self.teams = []
        self._teams_type = int
        self.scores = []
        self._scores_type = int

        self.set(**kwargs)

    def is_blue(self, team_number):
        '''Returns whether the team is on the blue alliance in this match'''
        return True if team_number in self.teams[0:2] else False

    def is_red(self, team_number):
        '''Returns whether the team is on the red alliance in this match'''
        return not self.is_blue(team_number)
