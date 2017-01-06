from data_models.data_model import DataModel
from data_models.strategy import Strategy


class MatchStrategy(DataModel):
    def __init__(self, **kwargs):
        self.match_number = -1
        self.auto = Strategy()
        self.teleop = []
        self.endgame = Strategy()

        self.__dict__.update(kwargs)
