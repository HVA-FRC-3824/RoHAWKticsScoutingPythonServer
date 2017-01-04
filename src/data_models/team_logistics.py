from .data_model import DataModel


class TeamLogistics(DataModel):
    def __init__(self, **kwargs):
        self.team_number = -1
        self.nickname = ""
        self.matches = []
        self.surrogate_match_number = -1

        self.__dict__.update(kwargs)
