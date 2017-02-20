from .data_model import DataModel


class SuperMatchData(DataModel):
    '''Data model that contains the data collect by a Super Scout for a match'''
    def __init__(self, d=None):
        DataModel.__init__(self)

        self.match_number = -1
        self.scout_name = ""

        self.blue_speed = []
        self.red_speed = []

        self.blue_torque = []
        self.red_torque = []

        self.blue_control = []
        self.red_control = []

        self.blue_defense = []
        self.red_defense = []

        self.notes = ""

        if d is not None:
            self.set(d)
