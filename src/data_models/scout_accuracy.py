from .data_model import DataModel


class ScoutAccuracy(DataModel):
    '''Data model that contains all the information about the error between this
       particular scouts data and `The Blue Alliance <thebluealliance.com>`_`'''
    def __init__(self, d=None):
        DataModel.__init__(self)

        self.name = ""
        self.scouted_matches = {}

        self.auto_mobility_error = 0
        self.auto_gear_error = 0
        self.teleop_gear_error = 0
        self.climb_error = 0

        if d is not None:
            self.set(d)

            temp = self.scouted_matches
            self.scouted_matches = {}
            for key, value in temp.__dict__.items():
                self.scouted_matches[key] = value

    def total(self):
        '''Tallies the error from each individual match scouted'''
        self.auto_mobility_error = 0
        self.auto_gear_error = 0
        self.teleop_gear_error = 0
        self.climb_error = 0

        for match in self.scouted_matches.values():
            self.auto_mobility_error += match.auto_mobility_error
            self.auto_gear_error += match.auto_rotor_error
            self.teleop_gear_error += match.teleop_rotor_error
            self.climb_error += match.endgame_error
