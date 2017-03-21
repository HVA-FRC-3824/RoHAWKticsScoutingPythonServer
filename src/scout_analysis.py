from the_blue_alliance import TheBlueAlliance
from database import Database
from data_models.scouted_match_accuracy import ScoutedMatchAccuracy
from data_models.scout_accuracy import ScoutAccuracy
from messenger import Messenger

import logging

from ourlogging import setup_logging
setup_logging(__file__)
logger = logging.getLogger(__name__)


class ScoutAnalysis:
    '''Thread class for determining scouting error

    Args:
        loop_time (`float`): Minumum time for a loop

    Kwargs:
        scouter_accuracy_config (`dict`): contains the error thresholds

        use_email (`bool`): whether to send reports via email

        emails (`list`): list of emails to send reports to

        use_texting (`bool`): whether to send reports via texting

        mobiles (`list`): list of phone numbers to send reports to

        login_file (`str`): location of the file containing the login information (not in the repo)

    '''
    TOTAL_THRESHOLD_DEFAULT = 10
    AUTO_THRESHOLD_DEFAULT = 10
    TELEOP_THRESHOLD_DEFAULT = 10
    ENDGAME_THRESHOLD_DEFAULT = 10

    shared_state = {}

    def __init__(self, **kwargs):
        self.__dict__ = self.shared_state
        if not hasattr(self, 'instance'):
            self.tba = TheBlueAlliance()
            self.database = Database()
            self.last_match = -1

            config = kwargs.get('scout_accuracy_config', None)
            if(config is not None):
                self.total_threshold = config.get('total_threshold', self.TOTAL_THRESHOLD_DEFAULT)
                self.auto_threshold = config.get('auto_threshold', self.AUTO_THRESHOLD_DEFAULT)
                self.telop_threshold = config.get('teleop_threshold', self.TELEOP_THRESHOLD_DEFAULT)
                self.endgame_threshold = config.get('endgame_threshold', self.ENDGAME_THRESHOLD_DEFAULT)
            else:
                self.total_threshold = self.TOTAL_THRESHOLD_DEFAULT
                self.auto_threshold = self.AUTO_THRESHOLD_DEFAULT
                self.teleop_threshold = self.TELEOP_THRESHOLD_DEFAULT
                self.endgame_threshold = self.ENDGAME_THRESHOLD_DEFAULT

            if kwargs.get('report_crash', False):
                self.messenger = Messenger(**kwargs)

            self.instance = True

    def analyze(self, match_number):
        match = self.database.get_match(match_number)

        # Haven't gotten match breakdown from TBA yet
        if match.score_breakdown is None:
            return False

        blue_teams = []
        red_teams = []

        for i, team_number in enumerate(match.team_numbers):
            if i < 3:
                blue_teams.append(self.database.get_team_match_data(match_number=match_number, team_number=team_number))
            else:
                red_teams.append(self.database.get_team_match_data(match_number=match_number, team_number=team_number))

        self.fuel_corrections(blue_teams, match.score_breakdown.blue)
        self.fuel_corrections(red_teams, match.score_breakdown.red)

        self.grade_scouts(match_number, "blue", blue_teams, match.score_breakdown.blue)
        self.grade_scouts(match_number, "red", red_teams, match.score_breakdown.red)

    def fuel_corrections(self, teams, score_breakdown):
        scouted_auto_high = 0
        scouted_auto_low = 0
        scouted_teleop_high = 0
        scouted_teleop_low = 0

        for team in teams:
            scouted_auto_high += team.auto_high_goal_made
            scouted_auto_low += team.auto_low_goal_made
            scouted_teleop_high += team.teleop_high_goal_made
            scouted_teleop_low += team.teleop_low_goal_made

        # correction is the number of ball not accounted for multiplied by the percent of the scouted fuel
        # this robot made
        for team in teams:
            team.auto_high_goal_correction = ((score_breakdown.autoFuelHigh - scouted_auto_high) *
                                              team.auto_high_goal_made / scouted_auto_high)
            team.auto_low_goal_correction = ((score_breakdown.autoFuelLow - scouted_auto_low) *
                                             team.auto_low_goal_made / scouted_auto_low)
            team.teleop_high_goal_correction = ((score_breakdown.teleopFuelHigh - scouted_teleop_high) *
                                                team.teleop_high_goal_made / scouted_teleop_high)
            team.teleop_low_goal_correction = ((score_breakdown.teleopFuelLow - scouted_teleop_low) *
                                               team.teleop_low_goal_made / scouted_teleop_low)
            self.database.set_team_match_data(team)

    def grade_scouts(self, match_number, alliance_color, teams, score_breakdown):
        sma = ScoutedMatchAccuracy()
        sma.match_number = match_number
        sma.alliance_color = alliance_color

        scouted_mobility = 0
        scouted_auto_gears = 0
        scouted_teleop_gears = 0
        scouted_climb = 0
        scouts = []

        for team in teams:
            scouts.append(team['scout_name'])
            scouted_mobility += 1 if team.auto_baseline else 0
            for gear in team.auto_gears:
                scouted_auto_gears += 1 if gear.placed else 0
            for gear in team.teleop_gears:
                scouted_teleop_gears += 1 if gear.placed else 0
            scouted_climb += 1 if team.endgame_climb == "successful" else 0

        error_message = ""

        # Check error for baseline
        sma.auto_mobility_error = score_breakdown.autoMobilityPoints / 5 - scouted_mobility
        if sma.auto_mobility_error != 0:
            error_message += ("Error: Incorrect number of baseline crosses for match {0:d} {1:s}.\n"
                              .format(match_number, alliance_color))
            error_message += ("Actual: {0:d} Scouted: {1:d} Error: {2:d}\n"
                              .format(score_breakdown.autoMobilityPoints / 5,
                                      scouted_mobility,
                                      sma.auto_mobility_error))

        if score_breakdown.autoRotorPoints == 120 and scouted_auto_gears != 3:
            error_message += ("Error: incorrect number of gears in auto for match {0:d} {1:s}.\n"
                              .format(match_number, alliance_color))
            error_message += ("Minimum possible number of gears: {0:d} Scouted number of gears: {1:d}"
                              .format(3, scouted_auto_gears))
            sma.auto_gear_error += 3 - scouted_auto_gears
        elif score_breakdown.autoRotorPoints == 60 and scouted_auto_gears < 1:
            error_message += ("Error: incorrect number of gears in auto for match {0:d} {1:s}.\n"
                              .format(match_number, alliance_color))
            error_message += ("Minimum possible number of gears: {0:d} Scouted number of gears: {1:d}"
                              .format(1, scouted_auto_gears))
            sma.auto_gear_error += 1 - scouted_auto_gears

        # 4 rotors takes at least 12 gears
        if score_breakdown.teleopRotorPoints == 160 and scouted_teleop_gears < 12:
            error_message += ("Error: incorrect number of gears in teleop for match {0:d} {1:s}.\n"
                              .format(match_number, alliance_color))
            error_message += ("Minimum possible number of gears: {0:d} Scouted number of gears: {1:d}"
                              .format(12, scouted_teleop_gears))
            sma.teleop_gear_error += 12 - scouted_teleop_gears
        # 3 rotors takes at least 6 gears
        elif score_breakdown.teleopRotorPoints == 120 and scouted_teleop_gears < 6:
            error_message += ("Error: incorrect number of gears in teleop for match {0:d} {1:s}.\n"
                              .format(match_number, alliance_color))
            error_message += ("Minimum possible number of gears: {0:d} Scouted number of gears: {1:d}"
                              .format(6, scouted_teleop_gears))
            sma.teleop_gear_error += 6 - scouted_teleop_gears
        # 2 rotors takes at least 2 gears
        elif score_breakdown.teleopRotorPoints == 80 and scouted_teleop_gears < 2:
            error_message += ("Error: incorrect number of gears in teleop for match {0:d} {1:s}.\n"
                              .format(match_number, alliance_color))
            error_message += ("Minimum possible number of gears: {0:d} Scouted number of gears: {1:d}"
                              .format(2, scouted_teleop_gears))
            sma.teleop_gear_error += 2 - scouted_teleop_gears
        # 40 points can be gotten without placing any

        sma.climb_error += score_breakdown.teleopTakeoffPoints / 50 - scouted_climb
        if sma.climb_error != 0:
            error_message += ("Error: incorrect number of climbs for match {0:d} {1:s}"
                              .format(match_number, alliance_color))
            error_message += ("Actual: {0:d} Scouted: {1:d} Error: {2:d}\n"
                              .format(score_breakdown.teleopTakeoffPoints / 50,
                                      scouted_climb,
                                      sma.climb_error))

        # Log errors to the screen
        for line in error_message.split('\n')[:-1]:
            logger.error(line)

        if len(error_message) > 0:
            logger.error("Scout Error: {0:d}) {1:s} - {2:s} - {3:s}"
                         .format(match_number,
                                 scouts[0],
                                 scouts[1],
                                 scouts[2]))
            if hasattr(self, 'messenger'):
                error_message += ("Scouters:\n\t{0:s}\n\t{1:s}\n\t{2:s}"
                                  .format(scouts[0],
                                          scouts[1],
                                          scouts[2]))
                self.messenger.send_message("Scout Error", error_message)

        # update scout error on firebase
        for i, scout_name in enumerate(scouts):
                    sma.alliance_number = i + 1
                    sa = self.database.get_scout_accuracy(scout_name)
                    if sa is None:
                        sa = ScoutAccuracy()
                        sa.name = scout_name
                    sa.scouted_matches['M' + str(match_number)] = sma
                    sa.total()
                    self.database.set_scout_accuracy(sa)
