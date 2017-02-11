import argparse
import time
import logging
import traceback
import signal
import os
import sys
import json
import threading
from threading import Event
from looper import Looper

from aggregator import Aggregator
from firebase_com import FirebaseCom
from the_blue_alliance import TheBlueAlliance
from socket_server import SocketServer
from scout_analysis import ScoutAnalysis
from constant import Constants
from messenger import Messenger

from data_models.match import Match
from data_models.team_logistics import TeamLogistics
from data_models.team_pit_data import TeamPitData
from data_models.team_ranking_data import TeamRankingData
from data_models.team_pick_ability import TeamPickAbility

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
            team_matches = Aggregator.set_matches(self.firebase, event_matches)
            logger.info("Added matches to Firebase")

            event_teams = self.tba.get_event_teams()
            Aggregator.set_teams(self.firebase, event_teams, team_matches)
            logger.info("Added teams to Firebase")

            event_rankings = self.tba.get_event_rankings()
            Aggregator.set_rankings(self.firebase, event_rankings)
            logger.info("Added rankings to Firebase")
        else:
            with open(os.path.dirname(os.path.abspath(__file__)) + "/../cached/" +
                      self.event_id + "/event_extras.json") as f:
                json_dict = json.loads(f.read())
                Constants().team_numbers = json_dict['team_numbers']
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
                    if self.crash_reporter:
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
                    if self.crash_reporter:
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
