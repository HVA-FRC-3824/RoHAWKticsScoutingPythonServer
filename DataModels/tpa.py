from .data_model import DataModel


class TPA(DataModel):
    def __init__(self, **kwargs):
        self.team_number = -1
        self.nickname = ""

        self.pick_ability = 0.0
        self.manual_ranking = -1

        self.top_line = ""
        self.second_line = ""
        self.third_line = ""

        self.robot_picture_filepath = ""

        self.yellow_card = False
        self.red_card = False
        self.stopped_moving = False

        self.picked = False
        self.dnp = False

        self.__dict__.update(kwargs)
