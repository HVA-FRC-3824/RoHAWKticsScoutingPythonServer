from .data_model import DataModel


class SMD(DataModel):
    def __init__(self, **kwargs):
        self.match_number = -1

        self.blue_speed = []
        self.red_speed = []

        self.blue_torque = []
        self.red_torque = []

        self.blue_control = []
        self.red_control = []

        self.blue_defense = []
        self.red_defense = []

        self.notes = ""

        self.__dict__.update(kwargs)
