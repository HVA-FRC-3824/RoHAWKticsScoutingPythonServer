from .data_model import DataModel
from .low_level_stats import LowLevelStats


class TeamCalculatedData(DataModel):
    '''All the calculated data for a team'''
    def __init__(self, **kwargs):
        self.team_number = -1

        self.total_points = LowLevelStats()

        # Autonomous
        self.auto_points = LowLevelStats()

        # Teleop
        self.teleop_points = LowLevelStats()

        # Endgame
        self.endgame_points = LowLevelStats()

        # Post Match
        self.no_show = LowLevelStats()
        self.stopped_moving = LowLevelStats()
        self.dq = LowLevelStats()

        # Fouls
        self.fouls = LowLevelStats()
        self.tech_fouls = LowLevelStats()
        self.yellow_cards = LowLevelStats()
        self.red_cards = LowLevelStats()

        # Qualitative
        self.zscore_speed = 0.0
        self.rank_speed = -1

        self.zscore_torque = 0.0
        self.rank_torque = -1

        self.zscore_control = 0.0
        self.rank_control = -1

        self.zscore_defense = 0.0
        self.rank_defense = -1

        self.__dict__.update(kwargs)
