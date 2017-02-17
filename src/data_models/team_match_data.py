from .data_model import DataModel
from .gear import Gear


class TeamMatchData(DataModel):
    '''Data collected by a match scout about a specific robot in a specific match'''
    def __init__(self, **kwargs):
        DataModel.__init__(self)

        self.team_number = -1
        self.match_number = -1
        self.alliance_color = ""
        self.allaince_number = -1
        self.scout_name = ""
        self.total_points = -1

        # Autonomous
        self.auto_start_position = ""
        self.auto_baseline = False
        self.auto_gears = []
        self._auto_gears_type = Gear()
        self.auto_high_goal_made = -1
        self.auto_high_goal_missed = -1
        self.auto_high_goal_correction = -1
        self.auto_low_goal_made = -1
        self.auto_low_goal_missed = -1
        self.auto_low_goal_correction = -1
        self.auto_hoppers = -1
        self.auto_points = -1

        # Teleop
        self.teleop_gears = []
        self._teleop_gears_type = Gear()
        self.teleop_high_goal_made = -1
        self.teleop_high_goal_missed = -1
        self.teleop_high_goal_correction = -1
        self.teleop_low_goal_made = -1
        self.teleop_low_goal_missed = -1
        self.teleop_low_goal_correction = -1
        self.teleop_hoppers = -1
        self.teleop_picked_up_gears = -1
        self.teleop_points = -1

        # Endgame
        self.endgame_climb = ""
        self.endgame_climb_time = ""
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

        self.set(**kwargs)
