from data_models.data_model import DataModel


class TBARecord(DataModel):
    def __init__(self, d=None):
        self.wins = 0
        self.ties = 0
        self.losses = 0
        if d is not None:
            self.set(d)
