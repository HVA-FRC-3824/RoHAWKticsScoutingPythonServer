from data_models.data_model import DataModel


class TBAAlliance(DataModel):
    def __init__(self, d=None):
        self.score = 0
        self.surrogate_team_keys = []
        self.team_keys = []
        if d is not None:
            self.set(d)
