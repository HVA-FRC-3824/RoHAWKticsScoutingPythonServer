from .data_model import DataModel


class TeamLogistics(DataModel):
    '''Logistics about a team collected from `The Blue Alliance <thebluealliance.com>_`'''
    def __init__(self, **kwargs):
        DataModel.__init__(self)

        self.team_number = -1
        self.nickname = ""
        self.match_numbers = []
        self.surrogate_match_number = -1

        self.set(**kwargs)
