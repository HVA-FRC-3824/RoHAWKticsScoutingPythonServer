from .data_model import DataModel


class ScoutedMatchAccuracy(DataModel):
    '''Data model that contains the information about a scouts data error when
       compared to `The Blue Alliance <thebluealliance.com>`_ for a specific match'''
    def __init__(self, **kwargs):
        self.match_number = -1
        self.alliance_color = ""
        self.alliance_number = -1

        self.total_error = -1
        self.auto_error = -1
        self.teleop_error = -1
        self.endgame_error = -1

        # Post Correction
        self.total_error_pc = -1
        self.auto_error_pc = -1
        self.teleop_error_pc = -1
        self.endgame_error_pc = -1

        self.set(**kwargs)
