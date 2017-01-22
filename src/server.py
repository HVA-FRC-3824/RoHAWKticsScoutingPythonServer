import argparse
import time
import logging
import traceback
import signal
import sys
import json
import threading
import scipy.stats as stats
from threading import Event
from looper import Looper
from functools import cmp_to_key

from aggregator import Aggregator
from firebase_com import FirebaseCom
from the_blue_alliance import TheBlueAlliance
from crash_reporter import CrashReporter
from socket_server import SocketServer
from scout_analysis import ScoutAnalysis

from data_models.match import Match
from data_models.alliance import Alliance
from data_models.team_logistics import TeamLogistics
from data_models.team_pit_data import TeamPitData
from data_models.team_ranking_data import TeamRankingData
from data_models.team_pick_ability import TeamPickAbility
from data_models.team_calculated_data import TeamCalculatedData
from data_models.low_level_stats import LowLevelStats

from calculators.team_calculator import TeamCalculator
from calculators.alliance_calculator import AllianceCalculator

from ourlogging import setup_logging

setup_logging(__file__)
logger = logging.getLogger(__name__)


class Server(Looper):
    '''Main server class that interprets the config file and starts various threads'''
    DEFAULT_TIME_BETWEEN_CYCLES = 60 * 4  # 4 minutes
    DEFAULT_TIME_BETWEEN_CACHES = 60 * 60 * 1  # 1 hour

    def __init__(self, **kwargs):
        ''' Initialization of all the server components based on the config

        Kwargs:
            The config json converted to a `dict`
        '''
        Looper.__init__(self)
        event_key = kwargs.get('event_key', "")
        logger.info("Event Key: {0:s}".format(event_key))
        self.event_key = event_key
        self.firebase = FirebaseCom(event_key)
        self.tba = TheBlueAlliance(event_key)
        self.event = None

        self.aggregate = kwargs.get('aggregate', False)

        if kwargs.get('messenger', False):
            self.messenger = Messenger(**kwargs)

        self.crash_reporter = kwargs.get('crash_reporter', False)
        self.cache_firebase = kwargs.get('cache_firebase', False)

        self.time_between_cycles = kwargs.get('time_between_cycles', self.DEFAULT_TIME_BETWEEN_CYCLES)
        self.time_between_caches = kwargs.get('time_between_caches', self.DEFAULT_TIME_BETWEEN_CACHES)

        self.set_loop_time(self.time_between_cycles)

        if kwargs.get('bluetooth', False):
            from bluetooth_server import BluetoothServer
            self.bluetooth = BluetoothServer()

        if kwargs.get('socket', False):
            self.socket = SocketServer()

        if kwargs.get('scouter_analysis', False):
            self.scout_analysis = ScoutAnalysis(**kwargs)

        if kwargs.get('setup', False):
            logger.info("Setting up database...")

            if self.tba.event_down():
                while True:
                    response = input("Event is down exit? (y/n)").lower()
                    if response in ['y', 'yes']:
                        sys.exit()
                    elif response in ['n', 'no']:
                        return

            event_matches = self.tba.get_event_matches()
            team_matches = self.set_matches(event_matches)
            logger.info("Added matches to Firebase")

            event_teams = self.tba.get_event_teams()
            self.set_teams(event_teams, team_matches)
            logger.info("Added teams to Firebase")

            event_rankings = self.tba.get_event_rankings()
            self.set_rankings(event_rankings)
            logger.info("Added rankings to Firebase")
        else:
            with open(os.path.dirname(os.path.abspath(__file__)) + "/../cached/"+ self.event_id + "/event_extras.json") as f:
                json_dict = json.loads(f.read())
                Constants().team_numbers = json_dict['team_number']
                Constants().number_of_matches = json_dict['number_of_matches']
                Constants().scout_names = json_dict['scout_names']

    def start(self):
        '''Starts the main thread loop'''
        self.event = None
        self.running = True
        self.on_tstart()
        while self.running:
            start_time = time.time()
            self.on_tloop()
            end_time = time.time()
            delta_time = end_time - start_time
            if self.loop_time - delta_time > 0 and self.running:
                self.event = Event()
                self.event.wait(timeout=self.loop_time - delta_time)
                self.event = None

    def set_matches(self, event_matches):
        '''Converts the match information pulled from `The Blue Alliance <thebluealliance.com>`_ into :class:`Match`

        Args:
            event_matches (dict): The match information pulled from `The Blue Alliance <thebluealliance.com>`_

        Returns:
                A `dict` containing all the match numbers for each team
        '''
        team_matches = {}
        number_of_matches = 0
        for tba_match in event_matches:
            if tba_match['comp_level'] != "qm":
                continue

            match = Match()
            match.match_number = tba_match['match_number']
            if match.match_number > number_of_matches:
                number_of_matches = match.match_number
            for color in ['blue', 'red']:
                for team_key in tba_match['alliances'][color]['teams']:
                    match.teams.append(int(team_key[3:]))
                match.scores.append(int(tba_match['alliances'][color]['score']))

            for team_number in match.teams:
                if team_number not in team_matches:
                    team_matches[team_number] = []
                team_matches[team_number].append(match.match_number)
            self.firebase.update_match(match)
            logger.info("Match {0:d} added".format(match.match_number))
        with open(os.path.dirname(os.path.abspath(__file__)) + "/../cached/"+ self.event_id + "/event_extras.json", "w") as f:
            json_dict = json.loads(f.read())
            json_dict['number_of_matches'] = number_of_matches
            f.write(json.loads(json_dict))
        Constants().number_of_matches = number_of_matches
        return team_matches

    def set_teams(self, event_teams, team_matches):
        '''Converts the team information from `The Blue Alliance <thebluealliance.com>`_
           to :class:`TeamLogistics`.

            Converts the team information from `The Blue Alliance <thebluealliance.com>`_
            to :class:`TeamLogistics`. Also, sets the match numbers for each team
            from the result of :func:`set_matches`

        Args:
            event_teams (dict): The team information from `The Blue Alliance <thebluealliance.com>`_

            team_matches (dict): The match numbers for each team

        '''
        team_logistics = []
        team_numbers = []

        for tba_team in event_teams:

            team_numbers.append(tba_team['team_number'])

            info = TeamLogistics()
            info.team_number = tba_team['team_number']
            info.nickname = tba_team['nickname']
            info.matches = team_matches[info.team_number]
            team_logistics.append(info)

            pit = TeamPitData()
            pit.team_number = info.team_number
            self.firebase.update_team_pit_data(pit)

            pick = TeamPickAbility()
            pick.team_number = info.team_number
            pick.nickname = info.nickname
            self.firebase.update_first_team_pick_ability(pick)
            self.firebase.update_second_team_pick_ability(pick)
            self.firebase.update_third_team_pick_ability(pick)
            logger.info("Team {0:d} added".format(info.team_number))

        min_matches = 100  # Each team should always have less than 100 matches
        for team in team_logistics:
            if len(team.matches) < min_matches:
                min_matches = len(team_matches)

        for team in team_logistics:
            if len(team.matches) > min_matches:
                team.surrogate_match_number = team.matches[3]
            self.firebase.update_team_logistics(info)
        with open(os.path.dirname(os.path.abspath(__file__)) + "/../cached/"+ self.event_id + "/event_extras.json", "w") as f:
            json_dict = json.loads(f.read())
            json_dict['team_numbers'] = team_numbers
            f.write(json.loads(json_dict))
        Constants().team_numbers = team_number

    def set_rankings(self, event_rankings):
        '''Convert the ranking information from `The Blue Alliance <thebluealliance.com>`_
           to the :class:`TeamRankingData`
        '''
        first = True
        for tba_ranking in list(event_rankings):
            if first:
                first = False
                continue
            tba_ranking_list = list(tba_ranking)
            ranking = TeamRankingData()
            ranking.team_number = int(tba_ranking_list[1])
            ranking.rank = int(tba_ranking_list[0])
            ranking.RPs = int(float(tba_ranking_list[2]))
            win_tie_lose = tba_ranking_list[7].split('-')
            ranking.wins = int(win_tie_lose[0])
            ranking.ties = int(win_tie_lose[2])
            ranking.loses = int(win_tie_lose[1])
            ranking.played = int(tba_ranking_list[8])
            self.firebase.update_current_team_ranking_data(ranking)
            logger.info("Added ranking for team {0:d}".format(ranking.team_number))

    def on_tstart(self):
        '''Runs before the main loop and starts the threads for :class:`BluetoothServer`,
           :class:`SocketServer`, and :class:`ScouterAnalysis` based on the config. Also,
           caches the firebase data.
        '''
        self.iteration = 1

        # initial run cache
        if self.cache_firebase:
            self.firebase.cache()
            self.time_since_last_cache = 0

        if hasattr(self, 'bluetooth'):
            self.bluetooth.start()

        if hasattr(self, 'socket'):
            self.socket.start()

    def on_tloop(self):
        '''Runs on each iteration of the main loop and aggregates the data.'''
        logger.info("Iteration {0:d}".format(self.iteration))
        if self.cache_firebase and self.time_between_caches < self.time_since_last_cache:
            self.firebase.cache()
            self.time_since_last_cache = 0

        start_time = time.time()
        if hasattr(self, 'scout_analysis'):
            try:
                self.scout_analysis.analyze_scouts()
            except:
                if self.running:
                    logger.error("Crash")
                    logger.error(traceback.format_exc())
                    if self.crash_reporter):
                        logger.error("Reporting crash")
                        try:
                            self.messenger.send_message("Server Crash!!!", traceback.format_exc())
                        # weird exception that doesn't stop the text
                        except:
                            pass

        if self.aggregate:
            try:
                Aggregator.make_team_calculations(self.firebase)
                Aggregator.make_super_calculations(self.firebase)
                Aggregator.make_pick_list_calculations(self.firebase)
            except:
                if self.running:
                    logger.error("Crash")
                    logger.error(traceback.format_exc())
                    if self.crash_reporter):
                        logger.error("Reporting crash")
                        try:
                            self.messenger.send_message("Server Crash!!!", traceback.format_exc())
                        # weird exception that doesn't stop the text
                        except:
                            pass

            if self.tba.event_down:
                if self.running:
                    logger.error("The Blue Alliance is down (possibly just for this event)")
                    self.messenger.send_message("The Blue Alliance is down (possibly just for this event)", "")
            else:
                try:
                    Aggregator.make_ranking_calculations(self.firebase, self.tba)
                except:
                    if self.running:
                        logger.error("Crash")
                        logger.error(traceback.format_exc())
                        if self.crash_reporter:
                            logger.error("Reporting crash")
                            try:
                                self.messenger.send_message("Server Crash!!!", traceback.format_exc())
                            # weird exception that doesn't stop the text
                            except:
                                pass

        end_time = time.time()
        time_taken = end_time - start_time
        logger.info("Iteration Ended")
        logger.info("Time taken: {0:f}s".format(time_taken))
        if self.time_between_cycles - time_taken > 0:
            self.event = threading.Event()
            self.event.wait(timeout=self.time_between_cycles - time_taken)
            self.event = None
        self.time_since_last_cache += self.time_between_cycles
        self.iteration += 1

    def stop(self):
        '''Stops all threads'''
        if hasattr(self, 'bluetooth'):
            self.bluetooth.stop()
        if hasattr(self, 'socket'):
            self.socket.stop()
        Looper.stop(self)

if __name__ == "__main__":
    # Collect command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--config", required=True, help="Config file with settings for the server")
    args = vars(ap.parse_args())

    f = open(args['config'])
    text = f.read()
    j = json.loads(text)

    server = Server(**j)

    def signal_handler(signal, frame):
        '''Catches control-c and cleanly shuts down the server'''
        logging.info("Control-C caught. Cleanly shutting down the server.")
        server.stop()
        sys.exit()
    signal.signal(signal.SIGINT, signal_handler)
    server.start()
