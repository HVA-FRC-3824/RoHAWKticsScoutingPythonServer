from .data_model import DataModel


class TPD(DataModel):
    def __init__(self, **kwargs):
        self.team_number = -1

        self.pit_scouted = False
        self.robot_image_filepath = ""
        self.robot_image_url = ""

        self.weight = 0.0
        self.width = 0.0
        self.length = 0.0
        self.height = 0.0

        self.programming_language = ""

        self.notes = ""

        self.__dict__.update(kwargs)
