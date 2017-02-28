from .data_model import DataModel
from .low_level_stats import LowLevelStats


class TeamCalculatedData(DataModel):
    '''All the calculated data for a team'''
    def __init__(self, d=None):
        DataModel.__init__(self)

        self.team_number = -1

        # Autonomous
        self.auto_baseline = LowLevelStats()
        self.auto_total_gears_placed = LowLevelStats()
        self.auto_near_gears_placed = LowLevelStats()
        self.auto_center_gears_placed = LowLevelStats()
        self.auto_far_gears_placed = LowLevelStats()
        self.auto_total_gears_dropped = LowLevelStats()
        self.auto_near_gears_dropped = LowLevelStats()
        self.auto_center_gears_dropped = LowLevelStats()
        self.auto_far_gears_dropped = LowLevelStats()
        self.auto_high_goal_made = LowLevelStats()
        self.auto_high_goal_missed = LowLevelStats()
        self.auto_low_goal_made = LowLevelStats()
        self.auto_low_goal_missed = LowLevelStats()
        self.auto_hoppers = LowLevelStats()
        self.auto_points = LowLevelStats()

        # Teleop
        self.teleop_total_gears_placed = LowLevelStats()
        self.teleop_near_gears_placed = LowLevelStats()
        self.teleop_center_gears_placed = LowLevelStats()
        self.teleop_far_gears_placed = LowLevelStats()
        self.teleop_total_gears_dropped = LowLevelStats()
        self.teleop_near_gears_dropped = LowLevelStats()
        self.teleop_center_gears_dropped = LowLevelStats()
        self.teleop_far_gears_dropped = LowLevelStats()
        self.teleop_high_goal_made = LowLevelStats()
        self.teleop_high_goal_missed = LowLevelStats()
        self.teleop_low_goal_made = LowLevelStats()
        self.teleop_low_goal_missed = LowLevelStats()
        self.teleop_hoppers = LowLevelStats()
        self.teleop_picked_up_gears = LowLevelStats()
        self.teleop_points = LowLevelStats()

        # Endgame
        self.endgame_climb_successful = LowLevelStats()
        self.endgame_climb_did_not_finish_in_time = LowLevelStats()
        self.endgame_climb_robot_fell = LowLevelStats()
        self.endgame_climb_no_attempt = LowLevelStats()
        self.endgame_climb_credited_through_foul = LowLevelStats()
        self.endgame_climb_time = LowLevelStats()
        self.endgame_points = LowLevelStats()

        self.total_points = LowLevelStats()

        # Post Match
        self.no_show = LowLevelStats()
        self.stopped_moving = LowLevelStats()
        self.dq = LowLevelStats()

        # Fouls
        self.fouls = LowLevelStats()
        self.tech_fouls = LowLevelStats()
        self.yellow_card = LowLevelStats()
        self.red_card = LowLevelStats()

        # Qualitative
        self.zscore_speed = 0.0
        self.rank_speed = -1

        self.zscore_torque = 0.0
        self.rank_torque = -1

        self.zscore_control = 0.0
        self.rank_control = -1

        self.zscore_defense = 0.0
        self.rank_defense = -1

        if d is not None:
            self.set(d)
