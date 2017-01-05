from .data_model import DataModel


class TeamDTFeedback(DataModel):
    '''Feedback given by the drive team about our alliance partners'''
    def __init__(self, **kwargs):
        self.team_number = -1
        self.feedback = {}

        self.__dict__.update(kwargs)
