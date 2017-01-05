from .data_model import DataModel


class TeamMatchData(DataModel):
    '''Data collected by a match scout about a specific robot in a specific match'''
    def __init__(self, **kwargs):
        self.team_number = -1
        self.match_number = -1
        self.alliance_color = ""
        self.allaince_number = -1
        self.scout_name = ""

        self.total_points = -1

        # Autonomous
        self.auto_points = -1

        # Teleop
        self.teleop_points = -1

        # Endgame
        self.endgame_points = -1

        # Post Match
        self.no_show = False
        self.stopped_moving = False
        self.dq = False
        self.notes = ""

        # Fouls
        self.fouls = 0
        self.tech_fouls = 0
        self.yellow_card = False
        self.red_card = False

        self.__dict__.update(kwargs)
