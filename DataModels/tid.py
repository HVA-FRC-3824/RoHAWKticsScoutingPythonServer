from .data_model import DataModel


class TID(DataModel):
    def __init__(self, **kwargs):
        self.team_number = -1
        self.nickname = ""
        self.matches = []

        self.__dict__.update(kwargs)
