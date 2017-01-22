from the_blue_alliance import TheBlueAlliance
from firebase_com import FirebaseCom
from data_models.scouted_match_accuracy import ScoutedMatchAccuracy

from twilio.rest import TwilioRestClient
import smtplib
import csv
import json
import logging
import os

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
            self.firebase = FirebaseCom()
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

            if kwargs.get('messenger', False):
                self.messenger = Messenger(**kwargs)

            self.instance = True

    def analyze_scouts(self):
        '''Calculates the error in the data for each alliance'''
        matches = self.tba.get_event_matches()
        matches = sorted(matches, key=lambda match: int(match['match_number']))
        for tba_match in matches:
            # Ignore elimination matches as we do not scout those
            if tba_match['comp_level'] != "qm":
                continue

            match_number = tba_match['match_number']
            logger.info("analyzing match {0:d}".format(match_number))

            # We have caught up to the current match
            if tba_match['alliances']['blue']['score'] == -1:
                self.last_match = match_number - 1
                logger.info("Last match: {0:d}".format(self.last_match))
                break

            # Each alliance gets graded separately
            for color in ['blue', 'red']:
                team_numbers = []
                for team_key in tba_match['alliances'][color]['teams']:
                    team_numbers.append(int(team_key[3:]))

                scout_scores = {}
                scout_scores['scout'] = []
                scout_scores['total'] = 0
                scout_scores['auto'] = 0
                scout_scores['teleop'] = 0
                scout_scores['endgame'] = 0
                incomplete = False
                firebase_teams = []
                for team_number in team_numbers:
                    firebase_team = self.firebase.get_team_match_data(team_number=team_number,
                                                                      match_number=match_number)
                    # don't grade is not all the data is in or if points have not been calculated
                    if(firebase_team.scout_name == "" or firebase_team.total_points == -1):
                        logger.info("Match {0:d} {1:s} incomplete".format(match_number, color))
                        incomplete = True
                        break

                    scout_scores['scout'].append(firebase_team.scout_name)
                    firebase_teams.append(firebase_team)

                # If incomplete move on to the next alliance
                if incomplete:
                    continue

                ##### Data Correction
                # TODO: get actual TBA keys
                tba_auto_high_balls = tba_match['score_breakdown'][color]['autoHighGoalBalls']
                tba_auto_low_balls = tba_match['score_breakdown'][color]['autoLowGoalBalls']
                tba_teleop_high_balls = tba_match['score_breakdown'][color]['teleopHighGoalBalls']
                tba_teleop_low_balls = tba_match['score_breakdown'][color]['teleopLowGoalBalls']
                actual_auto_high_balls = 0
                actual_auto_low_balls = 0
                actual_teleop_high_balls = 0
                actual_teleop_low_balls = 0

                for ft in firebase_teams:
                    actual_auto_high_balls += ft.auto_high_goal.made
                    actual_auto_low_balls += ft.auto_low_goal.made
                    actual_teleop_high_balls += ft.teleop_high_goal.made
                    actual_teleop_low_balls += ft.teleop_low_goal.low_goal_made

                # corrections are proportionally given based on the scouted ratios
                for ft in firebase_teams:
                    ft.auto_high_goal_correction.made = (tba_auto_high_balls - actual_auto_high_balls) * ft.auto_high_goal.made / actual_auto_high_balls
                    ft.auto_low_goal_correction.made = (tba_auto_low_balls - actual_auto_low_balls) * ft.auto_low_goal.made / actual_auto_low_balls
                    ft.teleop_high_goal_correction.made = (tba_teleop_high_balls - actual_teleop_high_balls) * ft.teleop_high_goal.made / actual_teleop_high_balls
                    ft.teleop_low_goal_correction.made = (tba_teleop_high_balls - actual_teleop_high_balls) * ft.teleop_high_goal.made / actual_teleop_high_balls
                    self.firebase.update_team_match_data(ft)
                scout_scores.update(self.calc_points(firebase_teams))

                #####################

                sma = ScoutedMatchAccuracy()
                sma.match_number = match_number
                sma.total_error = abs(tba_match['score_breakdown'][color]['totalPoints'] -
                                      tba_match['score_breakdown'][color]['foulPoints'] -
                                      scout_scores['total'])
                sma.auto_error = abs(tba_match['score_breakdown'][color]['autoPoints'] -
                                     scout_scores['auto'])
                sma.teleop_error = abs(tba_match['score_breakdown'][color]['teleopPoints'] -
                                       scout_scores['teleop'])
                sma.endgame_error = abs(tba_match['score_breakdown'][color]['endgamePoints'] -
                                         scout_scores['endgame'])

                error_message = ""

                if sma.total_error > self.total_threshold:
                    error_message += ("The total error for match {0:d} {1:s} exceeds the threshold.\n"
                                      .format(match_number, color))

                if sma.auto_error > self.auto_threshold:
                    error_message += ("The auto error for match {0:d} {1:s} exceeds the threshold.\n"
                                      .format(match_number, color))

                if sma.teleop_error > self.teleop_threshold:
                    error_message += ("The teleop error for match {0:d} {1:s} exceeds the threshold.\n"
                                      .format(match_number, color))

                if sma.endgame_error > self.endgame_threshold:
                    error_message += ("The endgame error for match {0:d} {1:s} exceeds the threshold.\n"
                                      .format(match_number, color))

                # Log errors to the screen
                for line in error_message.split('\n')[:-1]:
                    logger.error(line)

                if len(error_message) > 0:
                    logger.error("Scout Error: {0:d}) {0:s} - {1:s} - {2:s}"
                                 .format(match_number,
                                         scout_scores['scout'][0],
                                         scout_scores['scout'][1],
                                         scout_scores['scout'][2]))
                    if hasattr(self, 'messenger'):
                        error_message += ("Scouters:\n\t{0:s}\n\t{1:s}\n\t{2:s}"
                                          .format(scout_scores['scout'][0],
                                                  scout_scores['scout'][1],
                                                  scout_scores['scout'][2]))
                        self.messenger.send_message("Scout Error", error_message)

                for i, scout_name in enumerate(scout_scores['scout']):
                    sa = self.firebase.get_scout_accuracy(scout_name)
                    sma.alliance_color = color
                    sma.alliance_number = i + 1
                    sa.scouted_matches[match_number] = sma
                    sa.total()
                    self.firebase.update_scout_accuracy(sa)
        logger.info("Exporting scouter analysis")
        self.export()

    def calc_points(self, teams):
        points = {}
        points['auto'] = 0
        points['teleop'] = 0
        points['endgame'] = 0
        points['total'] = 0
        auto_gears = 0
        teleop_gears = 0
        for t in teams:
            for gear in t.auto_gears:
                if gear.placed:
                    auto_gears += 1
            for gear in t.teleop_gear:
                if gear.placed:
                    teleop_gears += 1
            points['auto'] += t.auto_high_goal.made + t.auto_low_goal.made / 3
            points['teleop'] += t.teleop_high_goal.made / 3 + t.teleop_low_goal.made / 9
            point['endgame'] += 50 if t.endgame_climb == "successful" else 0
        rotors = 0
        if auto_gears == 3:
            points['auto'] += 120
            rotors += 2
        elif auto_gears > 0:
            points['auto'] += 60
            rotors += 1

        if auto_gears + teleop_gears >= 12:
            points['teleop'] += (4 - rotors) * 40
        elif auto_gears + teleop_gears > 6:
            points['teleop'] += (3 - rotors) * 40
        elif auto_high_goal + teleop_gears > 2:
            points['teleop'] += (2 - rotors) * 40
        else:
            points['teleop'] += (1 - rotors) * 40

        points['auto'] = int(points['auto'])
        points['teleop'] = int(points['teleop'])
        return points



    def export(self):
        '''Exports the information to csv files (one overall and one for each scouter)'''
        fieldnames = ['scout_name', 'total_error', 'auto_error', 'teleop_error', 'endgame_error']
        export_dir = os.path.dirname(os.path.abspath(__file__)) + "/../"
        with open('{0:s}/scouting_accuracies/overall.csv'.format(export_dir), 'w') as overall:
            overall_writer = csv.writer(overall, fieldnames=fieldnames)
            fieldnames = ['match_number', 'alliance_color', 'alliance_number', 'total_error',
                          'auto_error', 'teleop_error', 'endgame_error']
            for scout in self.firebase.get_all_scout_accuracy():
                overall_writer.writerow(scout.to_dict())
                with open('{0:s}/scouting_accuracies/{1:s}.csv'
                          .format(export_dir, scout.scout_name), 'w') as scout_file:
                    scout_writer = csv.writer(scout_file, fieldnames=fieldnames)
                    for match in scout.scouted_matches.items():
                        scout_writer.writerow(match.to_dict())
