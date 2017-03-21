from .data_model import DataModel


class MatchPilotData(DataModel):
    def __init__(self, d=None):
        DataModel.__init__(self)
        self.match_number = -1
        self.teams = []

        if d is not None:
            self.set(d)
