from .data_model import DataModel


class TRD(DataModel):
    def __init__(self):
        self.team_number = -1

        self.rank = 0
        self.RPs = 0
        self.wins = 0
        self.ties = 0
        self.loses = 0
        self.played = 0
