from .data_model import DataModel


class TeamRankingData(DataModel):
    '''Data about a team's current or predicted ranking'''
    def __init__(self, d=None):
        DataModel.__init__(self)

        self.team_number = -1

        self.rank = 0
        self.RPs = 0
        self.wins = 0
        self.ties = 0
        self.loses = 0
        self.played = 0
        self.first_tie_breaker = 0
        self.second_tie_breaker = 0

        if d is not None:
            self.set(d)
