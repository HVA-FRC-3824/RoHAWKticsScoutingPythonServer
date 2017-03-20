from .data_model import DataModel
from .low_level_stats import LowLevelStats


class TeamCalculatedData(DataModel):
    '''All the calculated data for a team'''
    def __init__(self, d=None):
        DataModel.__init__(self)

        self.team_number = -1

        # Autonomous
        self.auto_start_position_far = 0
        self.auto_start_position_center = 0
        self.auto_start_position_near = 0
        self.auto_baseline = LowLevelStats()
        self.auto_gears = GearResults()
        self.auto_shooting = ShootingResults()
        self.auto_hoppers = LowLevelStats()
        self.auto_points = LowLevelStats()

        # Teleop
        self.teleop_gears = GearResults()
        self.teleop_shooting = ShootingResults()
        self.teleop_hoppers = LowLevelStats()
        self.teleop_picked_up_gears = LowLevelStats()
        self.teleop_points = LowLevelStats()

        # Endgame
        self.climb = ClimbResults()
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

        if d is not None:
            self.set(d)

    @staticmethod
    def from_list(tmds):
        rv = TeamCalculatedData()

        rv.team_number = tmds[0].team_number

        auto_baseline_list = []
        auto_gears_list = []
        auto_high_made = []
        auto_high_missed = []
        auto_low_made = []
        auto_low_missed = []
        auto_hoppers_list = []
        auto_points_list = []

        teleop_gears_list = []
        teleop_high_made = []
        teleop_high_missed = []
        teleop_low_made = []
        teleop_low_missed = []
        teleop_hoppers_list = []
        teleop_picked_up_gears_list = []
        teleop_points_list = []

        climb_result_list = []
        climb_time_list = []
        endgame_points_list = []

        no_show_list = []
        stopped_moving_list = []
        dq_list = []

        fouls_list = []
        tech_fouls_list = []
        yellow_cards_list = []
        red_cards_list = []

        for tmd in tmds:

            if tmd.auto_start_position == "Near":
                rv.auto_start_position_near += 1
            elif tmd.auto_start_position == "Center":
                rv.auto_start_position_center += 1
            elif tmd.auto_start_position == "Far":
                rv.auto_start_position_far += 1
            else:
                logger.error("Unknown start position")

            auto_baseline_list.append(tmd.auto_baseline)
            auto_gears_list.append(tmd.auto_gears)
            auto_high_made.append(tmd.auto_high_made + auto_high_correction)
            auto_high_missed.append(tmd.auto_high_missed)
            auto_low_made.append(tmd.auto_low_made + auto_low_correction)
            auto_low_missed.append(tmd.auto_low_missed)
            auto_hoppers_list.append(tmd.auto_hoppers)
            auto_points_list.append(tmd.auto_points)

            teleop_high_made.append(tmd.teleop_high_made + tmd.teleop_high_correction)
            teleop_high_missed.append(tmd.teleop_high_missed)
            teleop_low_made.append(tmd.teleop_low_made + tmd.teleop_low_correction)
            teleop_low_missed.append(tmd.teleop_low_missed)
            teleop_hoppers_list.append(tmd.teleop_hoppers)
            teleop_picked_up_gears_list.append(tmd.teleop_picked_up_gears)
            teleop_points_list.append(tmd.teleop_points)

            climb_result_list.append(tmd.endgame_climb)
            climb_time_list.append(tmd.endgame_climb_time)
            endgame_points_list.append(tmd.endgame_points)

            no_show_list.append(tmd.no_show)
            stopped_moving_list.append(stopped_moving)
            dq_list.append(tmd.dq)

            fouls_list.append(tmd.fouls)
            tech_fouls_list.append(tmd.tech_fouls)
            yellow_cards_list.append(tmd.yellow_card)
            red_cards_list.append(tmd.red_card)

        rv.auto_baseline = LowLevelStats.from_list(auto_baseline_list)
        rv.auto_gears = GearResults.from_list(auto_gears_list)
        rv.auto_shooting = ShootingResults.from_lists(auto_high_made, auto_high_missed, auto_low_made, auto_low_missed)
        rv.auto_hoppers = LowLevelStats.from_list(auto_hoppers_list)
        rv.auto_points = LowLevelStats.from_list(auto_points_list)

        rv.teleop_gears = GearResults.from_list(teleop_gears_list)
        rv.teleop_shooting = ShootingResults.from_lists(teleop_high_made, teleop_high_missed, teleop_low_made, teleop_low_missed)
        rv.teleop_hoppers = LowLevelStats.from_list(teleop_hoppers_list)
        rv.teleop_picked_up_gears = LowLevelStats.from_list(teleop_picked_up_gears_list)
        rv.teleop_points = LowLevelStats.from_list(teleop_points_list)

        rv.climb = ClimbResults.from_lists(climb_result_list, climb_time_list)
        rv.endgame_points = LowLevelStats.from_list(endgame_points_list)

        rv.no_show = LowLevelStats.from_list(no_show_list)
        rv.stopped_moving = LowLevelStats.from_list(stopped_moving_list)
        rv.dq = LowLevelStats.from_list(dq_list)

        rv.fouls = LowLevelStats.from_list(fouls_list)
        rv.tech_fouls = LowLevelStats.from_list(tech_fouls_list)
        rv.yellow_cards = LowLevelStats.from_list(yellow_cards_list)
        rv.red_cards = LowLevelStats.from_list(red_cards_list)

        return rv
