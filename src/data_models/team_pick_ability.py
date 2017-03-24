from .data_model import DataModel
from database import Database
from calculators.team_calculator import TeamCalculator


class TeamPickAbility(DataModel):
    '''Data about a team's strength as a specific type of pick'''
    def __init__(self, d=None):
        DataModel.__init__(self)

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

        if d is not None:
            self.set(d)

    @staticmethod
    def calculate_first_pick_ability(team_number):
        tpa = TeamPickAbility()
        tpa.team_number = team_number

        database = Database()

        tc = TeamCalculator(team_number)

        tpa.pick_ability = tc.first_pick_ability()

        pit = database.get_team_pit_data(team_number)

        if(pit.robot_picture_default > -1 and pit.robot_picture_default < len(pit.robot_pictures)):
            tpa.robot_picture_filepath = pit.robot_pictures[pit.robot_picture_default].filepath

        calc = database.get_team_calculated_data(team_number)
        tpa.yellow_card = calc.yellow_card.total > 0
        tpa.red_card = calc.red_card.total > 0
        tpa.stopped_moving = calc.stopped_moving.total > 1
        tpa.top_line = ("PA: {0:0.2f} Average High Goal Balls: Auto {1:0.2f}, Teleop {2:0.2f}"
                        .format(tpa.pick_ability, calc.auto_shooting.high.made.average,
                                calc.teleop_shooting.high.made.average))
        tpa.second_line = ("Average Gears: Auto {0:0.2f}, Teleop {1:0.2f}"
                           .format(calc.auto_gears.total.placed.average,
                                   calc.teleop_gears.total.placed.average))
        tpa.third_line = ("Climb: Success Percentage {0:0.2f}%, Time {1:0.2f}s"
                          .format(calc.climb.success_percentage, calc.climb.time.average))
        tpa.fourth_line = ""
        return tpa

    @staticmethod
    def calculate_second_pick_ability(team_number):
        tpa = TeamPickAbility()
        tpa.team_number = team_number

        database = Database()

        tc = TeamCalculator(team_number)

        tpa.pick_ability = tc.second_pick_ability()

        pit = database.get_team_pit_data(team_number)

        if(pit.robot_picture_default > -1 and pit.robot_picture_default < len(pit.robot_pictures)):
            tpa.robot_picture_filepath = pit.robot_pictures[pit.robot_picture_default].filepath

        calc = database.get_team_calculated_data(team_number)
        tpa.yellow_card = calc.yellow_card.total > 0
        tpa.red_card = calc.red_card.total > 0
        tpa.stopped_moving = calc.stopped_moving.total > 1

        qual = database.get_team_qualitative_data(team_number)

        tpa.top_line = ("PA: {0:0.2f} Defense: {1:d} Control: {2:d} Speed: {3:d} Torque: {3:d}"
                        .format(tpa.pick_ability,
                                qual.defense.rank,
                                qual.control.rank,
                                qual.speed.rank,
                                qual.torque.rank))
        tpa.second_line = ("Average Gears: Auto {0:0.2f}, Teleop {1:0.2f}"
                           .format(calc.auto_gears.total.placed.average,
                                   calc.teleop_gears.total.placed.average))
        tpa.third_line = ("Climb: Success Percentage {0:0.2f}%, Time {1:0.2f}s"
                          .format(calc.climb.success_percentage, calc.climb.time.average))
        tpa.fourth_line = ("Weight: {0:0.2f} lbs, PL: {1:s}"
                           .format(pit.weight, pit.programming_language))
        return tpa

    @staticmethod
    def calculate_third_pick_ability(team_number):
        tpa = TeamPickAbility()
        tpa.team_number = team_number

        database = Database()

        tc = TeamCalculator(team_number)

        tpa.pick_ability = tc.third_pick_ability()

        pit = database.get_team_pit_data(team_number)

        if(pit.robot_picture_default > -1 and pit.robot_picture_default < len(pit.robot_pictures)):
            tpa.robot_picture_filepath = pit.robot_pictures[pit.robot_picture_default].filepath

        calc = database.get_team_calculated_data(team_number)
        tpa.yellow_card = calc.yellow_card.total > 0
        tpa.red_card = calc.red_card.total > 0
        tpa.stopped_moving = calc.stopped_moving.total > 1
        tpa.top_line = ("PA: {0:0.2f} Average High Goal Balls: Auto {1:0.2f}, Teleop {2:0.2f}"
                        .format(tpa.pick_ability, calc.auto_shooting.high.made.average,
                                calc.teleop_shooting.high.made.average))
        tpa.second_line = ("Average Gears: Auto {0:0.2f}, Teleop {1:0.2f}"
                           .format(calc.auto_gears.total.placed.average,
                                   calc.teleop_gears.total.placed.average))
        tpa.third_line = ("Climb: Success Percentage {0:0.2f}%, Time {1:0.2f}s"
                          .format(calc.climb.success_percentage, calc.climb.time.average))
        tpa.fourth_line = ("Weight: {0:0.2f} lbs, PL: {1:s}"
                           .format(pit.weight, pit.programming_language))
        return tpa
