from looper import Looper
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


class ScouterAnalysis(Looper):
    TOTAL_THRESHOLD_DEFAULT = 10
    AUTO_THRESHOLD_DEFAULT = 10
    TELEOP_THRESHOLD_DEFAULT = 10
    ENDGAME_THRESHOLD_DEFAULT = 10

    shared_state = {}

    def __init__(self, loop_time=None, **configs):
        self.__dict__ = self.shared_state
        if not hasattr(self, 'instance'):
            Looper.__init__(self)
            self.tba = TheBlueAlliance()
            self.firebase = FirebaseCom()
            self.last_match = -1
            self.loop_time = loop_time

            sa_config = configs.get('scouter_accuracy_config', None)
            if(sa_config is not None):
                self.total_threshold = sa_config.get('total_threshold', self.TOTAL_THRESHOLD_DEFAULT)
                self.auto_threshold = sa_config.get('auto_threshold', self.AUTO_THRESHOLD_DEFAULT)
                self.telop_threshold = sa_config.get('teleop_threshold', self.TELEOP_THRESHOLD_DEFAULT)
                self.endgame_threshold = sa_config.get('endgame_threshold', self.ENDGAME_THRESHOLD_DEFAULT)
            else:
                self.total_threshold = self.TOTAL_THRESHOLD_DEFAULT
                self.auto_threshold = self.AUTO_THRESHOLD_DEFAULT
                self.teleop_threshold = self.TELEOP_THRESHOLD_DEFAULT
                self.endgame_threshold = self.ENDGAME_THRESHOLD_DEFAULT

            self.use_email = configs.get('use_email', True)
            self.emails = configs.get('emails', ['akmessing1@yahoo.com'])
            f = open(os.path.dirname(__file__) + "/" + configs.get('logins_file', '../logins.json'))
            json_dict = json.loads(f.read())
            self.gmail_user = json_dict['gmail_user']
            self.gmail_password = json_dict['gmail_password']

            self.smtp = smtplib.SMTP("smtp.gmail.com", 587)
            self.smtp.ehlo()
            self.smtp.starttls()
            self.smtp.ehlo()
            self.smtp.login(self.gmail_user, self.gmail_password)

            self.twilio_sid = json_dict['twilio_sid']
            self.twilio_token = json_dict['twilio_token']
            self.twilio_number = json_dict['twilio_number']
            logger.info(self.twilio_sid)
            logger.info(self.twilio_token)
            logger.info(self.twilio_number)
            self.client = TwilioRestClient(self.twilio_sid, self.twilio_token)

            self.use_texting = configs.get('use_texting', True)
            self.mobiles = configs.get('mobiles', ['8659631368'])

            self.instance = True

    def start(self):
        self.tstart()

    def stop(self):
        if self.use_email:
            self.smtp.close()
        Looper.stop(self)

    def on_tstart(self):
        logger.info("Scout Analysis thread starting")

    def on_tloop(self):
        matches = self.tba.get_event_matches()
        matches = sorted(matches, key=lambda match: int(match['match_number']))
        for tba_match in matches:
            if tba_match['comp_level'] != "qm":
                continue

            match_number = tba_match['match_number']
            logger.info("analyzing match {0:d}".format(match_number))
            # We have caught up to the current match
            if tba_match['alliances']['blue']['score'] == -1:
                self.last_match = match_number - 1
                logger.info("Last match: {0:d}".format(self.last_match))
                break

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
                for team_number in team_numbers:
                    firebase_team = self.firebase.get_team_match_data(team_number=team_number,
                                                                      match_number=match_number)
                    if(firebase_team.scout_name == ""):
                        logger.info("Match {0:d} {1:s} incomplete".format(match_number, color))
                        incomplete = True
                        break
                    scout_scores['scout'].append(firebase_team.scout_name)
                    scout_scores['total'] += 0
                    scout_scores['auto'] += 0
                    scout_scores['teleop'] += 0
                    scout_scores['endgame'] += 0

                if incomplete:
                    continue

                sma = ScoutedMatchAccuracy()
                sma.match_number = match_number
                sma.total_error = abs(tba_match['score_breakdown'][color]['totalPoints'] -
                                      tba_match['score_breakdown'][color]['foulPoints'] -
                                      scout_scores['total'])
                sma.auto_error = abs(tba_match['score_breakdown'][color]['autoPoints'] -
                                     scout_scores['auto'])
                sma.teleop_error = abs(tba_match['score_breakdown'][color]['teleopPoints'] -
                                       scout_scores['teleop'])
                # sma.endgame_error = abs(tba_match['score_breakdown'][color]['endgamePoints'] -
                #                         scout_scores['endgame'])

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

                for line in error_message.split('\n')[:-1]:
                    logger.error(line)

                if len(error_message) > 0:
                    error_message += ("Scouters:\n\t{0:s}\n\t{1:s}\n\t{2:s}"
                                      .format(scout_scores['scout'][0],
                                              scout_scores['scout'][1],
                                              scout_scores['scout'][2]))
                    logger.error("Scouter:\t{0:s}\t{1:s}\t{2:s}"
                                 .format(scout_scores['scout'][0],
                                         scout_scores['scout'][1],
                                         scout_scores['scout'][2]))
                    self.report_error(error_message)

                for i, scout_name in enumerate(scout_scores['scout']):
                    sa = self.firebase.get_scout_accuracy(scout_name)
                    sma.alliance_color = color
                    sma.alliance_number = i + 1
                    sa.scouted_matches[match_number] = sma
                    sa.total()
                    self.firebase.update_scout_accuracy(sa)
        logger.info("Exporting scouter analysis")
        self.export()

    def export(self):
        fieldnames = ['scout_name', 'total_error', 'auto_error', 'teleop_error', 'endgame_error']
        with open('scout_accuracies/overall.csv', 'w') as overall:
            overall_writer = csv.writer(overall, fieldnames=fieldnames)
            fieldnames = ['match_number', 'alliance_color', 'alliance_number', 'total_error',
                          'auto_error', 'teleop_error', 'endgame_error']
            for scout in self.firebase.get_all_scout_accuracy():
                overall_writer.writerow(scout.to_dict())
                with open('scout_accuracies/{0:s}.csv'.format(scout.scout_name), 'w') as scout_file:
                    scout_writer = csv.writer(scout_file, fieldnames=fieldnames)
                for match in scout.scouted_matches.items():
                    scout_writer.writerow(match.to_dict())

    def report_error(self, message):
        if self.use_email:
            self.email_report(message)
        if self.use_texting:
            self.text_report(message)

    def email_report(self, message):
        header = ("To:{0:s}\nFrom:{1:s}\nSubject: Scout Error\n"
                  .format(', '.join(self.emails), self.gmail_user))
        msg = header + '\n' + message
        self.smtp.sendmail(self.gmail_user, self.emails, msg)

    def text_report(self, message):
        for phone_number in self.mobiles:
            self.client.messages.create(to=phone_number,
                                        from_=self.twilio_number,
                                        body="Scout Error\n{0:s}".format(message))
