from .data_model import DataModel


class ScoutedMatchAccuracy(DataModel):
    def __init__(self, **kwargs):
        self.match_number = -1
        self.alliance_color = ""
        self.alliance_number = -1

        self.total_error = -1
        self.auto_error = -1
        self.teleop_error = -1
        self.endgame_error = -1

        self.__dict__.update(**kwargs)
