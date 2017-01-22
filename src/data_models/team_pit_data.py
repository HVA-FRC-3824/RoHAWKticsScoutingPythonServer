from .data_model import DataModel


class TeamPitData(DataModel):
    '''Data collected by pit scouts'''
    def __init__(self, **kwargs):
        self.team_number = -1
        self.scout_name = ""

        self.robot_image_default = -1
        self.robot_image_filepaths = []
        self.robot_image_urls = []

        self.weight = 0.0
        self.width = 0.0
        self.length = 0.0
        self.height = 0.0

        self.programming_language = ""

        self.notes = ""

        self.set(**kwargs)
