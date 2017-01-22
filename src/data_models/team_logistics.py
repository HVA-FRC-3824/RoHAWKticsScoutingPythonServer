from .data_model import DataModel


class TeamLogistics(DataModel):
    '''Logistics about a team collected from `The Blue Alliance <thebluealliance.com>_`'''
    def __init__(self, **kwargs):
        self.team_number = -1
        self.nickname = ""
        self.matches = []
        self.surrogate_match_number = -1

        self.set(**kwargs)
