from .data_model import DataModel


class MatchTeamPilotData(DataModel):
    def __init__(self, d=None):
        DataModel.__init__(self)
        self.team_number = -1
        self.rating = ""
        self.drops = 0
        self.lifts = 0

        if d is not None:
            self.set(d)
