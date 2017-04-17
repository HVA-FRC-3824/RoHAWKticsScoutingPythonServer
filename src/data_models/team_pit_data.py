from .data_model import DataModel


class TeamPitData(DataModel):
    '''Data collected by pit scouts'''
    def __init__(self, d=None):
        DataModel.__init__(self)

        self.team_number = -1
        self.scout_name = ""

        self.robot_picture_default = ""
        self.robot_pictures = []

        self.weight = 0.0
        self.width = 0.0
        self.length = 0.0
        self.height = 0.0

        self.programming_language = ""

        self.notes = ""

        if d is not None:
            self.set(d)
