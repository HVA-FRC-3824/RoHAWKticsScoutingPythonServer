from .data_model import DataModel


class ScoutedMatchAccuracy(DataModel):
    '''Data model that contains the information about a scouts data error when
       compared to `The Blue Alliance <thebluealliance.com>`_ for a specific match'''
    def __init__(self, d=None):
        self.match_number = -1
        self.alliance_color = ""
        self.alliance_number = -1

        self.total_error = 0
        self.auto_mobility_error = 0
        self.auto_rotor_error = 0
        self.teleop_rotor_error = 0
        self.endgame_error = 0

        if d is not None:
            self.set(d)
