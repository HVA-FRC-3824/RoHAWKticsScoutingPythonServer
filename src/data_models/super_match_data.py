from .data_model import DataModel


class SuperMatchData(DataModel):
    '''Data model that contains the data collect by a Super Scout for a match'''
    def __init__(self, d=None):
        DataModel.__init__(self)

        self.match_number = -1
        self.scout_name = ""

        self.blue_speed = {}
        self.red_speed = {}

        self.blue_torque = {}
        self.red_torque = {}

        self.blue_control = {}
        self.red_control = {}

        self.blue_defense = {}
        self.red_defense = {}

        self.notes = ""

        if d is not None:
            self.set(d)

            temp = self.blue_speed
            self.blue_speed = {}
            for key, value in temp.__dict__.items():
                self.blue_speed[key] = value

            temp = self.red_speed
            self.red_speed = {}
            for key, value in temp.__dict__.items():
                self.red_speed[key] = value

            temp = self.blue_torque
            self.blue_torque = {}
            for key, value in temp.__dict__.items():
                self.blue_torque[key] = value

            temp = self.red_torque
            self.red_torque = {}
            for key, value in temp.__dict__.items():
                self.red_torque[key] = value

            temp = self.blue_control
            self.blue_control = {}
            for key, value in temp.__dict__.items():
                self.blue_control[key] = value

            temp = self.red_control
            self.red_control = {}
            for key, value in temp.__dict__.items():
                self.red_control[key] = value

            temp = self.blue_defense
            self.blue_defense = {}
            for key, value in temp.__dict__.items():
                self.blue_defense[key] = value

            temp = self.red_defense
            self.red_defense = {}
            for key, value in temp.__dict__.items():
                self.red_defense[key] = value
