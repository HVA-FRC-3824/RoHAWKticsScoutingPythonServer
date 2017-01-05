from .data_model import DataModel


class ScoutAccuracy(DataModel):
    '''Data model that contains all the information about the error between this
       particular scouts data and `The Blue Alliance <thebluealliance.com>`_`'''
    def __init__(self, **kwargs):
        self.name = ""
        self.scouted_matches = {}

        self.total_error = 0
        self.auto_error = 0
        self.teleop_error = 0
        self.endgame_error = 0

        self.__dict__.update(**kwargs)

    def total(self):
        '''Tallies the error from each individual match scouted'''
        self.total_error = 0
        self.auto_error = 0
        self.teleop_error = 0
        self.endgame_error = 0

        for match in self.scouted_matches.values():
            print(match.total_error)
            self.total_error += match.total_error
            self.auto_error += match.auto_error
            self.teleop_error += match.teleop_error
            self.endgame_error += match.endgame_error
