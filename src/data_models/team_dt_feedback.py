from .data_model import DataModel


class TeamDTFeedback(DataModel):
    def __init__(self, **kwargs):
        self.team_number = -1
        self.feedback = {}

        self.__dict__.update(kwargs)
