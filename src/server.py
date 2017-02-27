import argparse
import time
import logging
import traceback
import signal
import os
import sys
import json
from urllib.request import urlopen
from threading import Event
from looper import Looper

from aggregator import Aggregator
from firebase_com import FirebaseCom
from the_blue_alliance import TheBlueAlliance
from socket_server import SocketServer
from scout_analysis import ScoutAnalysis
from constants import Constants
from messenger import Messenger
from led_manager import LedManager

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
        self.event_key = kwargs.get('event_key', "")
        if self.event_key == "":
            logger.critical("No event key")
            sys.exit()
        logger.info("Event Key: {0:s}".format(self.event_key))

        self.led_manager = LedManager()
        self.led_manager.starting_up()

        self.firebase = FirebaseCom(self.event_key)
        self.tba = TheBlueAlliance(self.event_key)

        # event for threading not FIRST event
        self.event = None

        self.aggregate = kwargs.get('aggregate', False)

        # if kwargs.get('messenger', False):
        self.messenger = Messenger(**kwargs)

        self.report_crash = kwargs.get('report_crash', False)
        self.cache_firebase = kwargs.get('cache_firebase', False)
        if self.cache_firebase:
            self.time_between_caches = kwargs.get('time_between_caches', self.DEFAULT_TIME_BETWEEN_CACHES)

        self.time_between_cycles = kwargs.get('time_between_cycles', self.DEFAULT_TIME_BETWEEN_CYCLES)

        self.set_loop_time(self.time_between_cycles)

        if kwargs.get('bluetooth', False):
            from bluetooth_server import BluetoothServer
            self.bluetooth = BluetoothServer()

        if kwargs.get('socket', False):
            self.socket = SocketServer()

        if kwargs.get('scout_analysis', False):
            self.scout_analysis = ScoutAnalysis(**kwargs)

        if kwargs.get('setup', False):
            logger.info("Setting up database...")

            if self.tba.event_down():
                while True:
                    response = input("Event is down. Exit? (y/n)").lower()
                    if response in ['y', 'yes']:
                        sys.exit()
                    elif response in ['n', 'no']:
                        return

            event_matches = self.tba.get_event_matches()
            team_matches, team_surrogate_matches, num_matches = Aggregator.set_matches(self.firebase, event_matches)
            logger.info("Added matches to Firebase")

            event_teams = self.tba.get_event_teams()
            team_numbers = Aggregator.set_teams(self.firebase, event_teams, team_matches, team_surrogate_matches)
            logger.info("Added teams to Firebase")

            event_rankings = self.tba.get_event_rankings()
            Aggregator.set_rankings(self.firebase, event_rankings)
            logger.info("Added rankings to Firebase")

            with open(os.path.dirname(os.path.abspath(__file__)) + "/../cached/" +
                      self.event_key + "/event_extras.json", 'w') as f:
                json_dict = {}
                json_dict['number_of_matches'] = num_matches
                json_dict['team_numbers'] = team_numbers
                f.write(json.dumps(json_dict, sort_keys=True, indent=4))

            logger.info("Exiting...")
            os._exit(0)
        else:
            with open(os.path.dirname(os.path.abspath(__file__)) + "/../cached/" +
                      self.event_key + "/event_extras.json") as f:
                json_dict = json.loads(f.read())
                # Constants is a singleton
                Constants().team_numbers = json_dict['team_numbers']
                Constants().number_of_matches = json_dict['number_of_matches']

    def start(self):
        '''Starts the main thread loop'''
        self.led_manager.start_up_complete()
        self.event = None
        self.running = True
        self.on_tstart()
        iteration = 1
        while self.running:
            logger.info("Iteration {0:d}".format(iteration))
            start_time = time.time()
            self.on_tloop()
            end_time = time.time()
            delta_time = end_time - start_time
            logger.info("Iteration Ended")
            logger.info("Time taken: {0:f}s".format(delta_time))
            iteration += 1
            if self.loop_time - delta_time > 0 and self.running:
                # Event is used, so that we can stop the loop early if quitting
                self.event = Event()
                self.event.wait(timeout=self.loop_time - delta_time)
                self.event = None

    def on_tstart(self):
        '''Runs before the main loop and starts the threads for :class:`BluetoothServer`,
           :class:`SocketServer`, and :class:`ScouterAnalysis` based on the config. Also,
           caches the firebase data.
        '''
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

        if self.cache_firebase and self.time_between_caches < self.time_since_last_cache:
            self.firebase.cache()
            self.time_since_last_cache = 0

        if self.tba.event_down():
            try:
                urlopen('http://216.58.192.142', timeout=1)
                self.led_manager.tba_down()
                logger.warning("The Blue Alliance is down (possibly just for this event)")
                self.messenger.send_message("The Blue Alliance is down (possibly just for this event)")
            except:
                self.led_manager.internet_connection_down()
                logger.warning("Internet connection is down")
        elif hasattr(self, 'scout_analysis'):
            self.led_manager.internet_connected()
            try:
                logger.info("Analyzing scouts")
                self.scout_analysis.analyze_scouts()
            except:
                self.led_manager.error()
                if self.running:
                    logger.error("Crash")
                    logger.error(traceback.format_exc())
                    if self.report_crash:
                        logger.error("Reporting crash")
                        self.messenger.send_message("Server Crash!!!", traceback.format_exc())
        if not self.running:
            return

        if self.aggregate:
            logger.info("Aggregating")
            try:
                logger.info("Making match calculations")
                Aggregator.make_team_calculations(self.firebase)

                if not self.running:
                    return

                logger.info("Making super match calculations")
                Aggregator.make_super_calculations(self.firebase)

                if not self.running:
                    return

                logger.info("Making pick list calculations")
                Aggregator.make_pick_list_calculations(self.firebase)

                if not self.running:
                    return
            except:
                self.led_manager.error()
                if self.running:
                    logger.error("Crash")
                    logger.error(traceback.format_exc())
                    if self.report_crash:
                        logger.error("Reporting crash")
                        self.messenger.send_message("Server Crash!!!", traceback.format_exc())

            if not self.running:
                return

            if self.tba.event_down():
                try:
                    urlopen('http://216.58.192.142', timeout=1)
                    self.led_manager.tba_down()
                    logger.warning("The Blue Alliance is down (possibly just for this event)")
                    self.messenger.send_message("The Blue Alliance is down (possibly just for this event)")
                except:
                    self.led_manager.internet_connection_down()
                    logger.warning("Internet connection is down")
            else:
                try:
                    logger.info("Making ranking calculations")
                    Aggregator.make_ranking_calculations(self.firebase, self.tba)
                except:
                    self.led_manager.error()
                    if self.running:
                        logger.error("Crash")
                        logger.error(traceback.format_exc())
                        if self.report_crash:
                            logger.error("Reporting crash")
                            self.messenger.send_message("Server Crash!!!", traceback.format_exc())

        if self.cache_firebase:
            self.time_since_last_cache += self.time_between_cycles

    def stop(self):
        '''Stops all threads'''
        if hasattr(self, 'bluetooth'):
            self.bluetooth.stop()
        if hasattr(self, 'socket'):
            self.socket.stop()
        self.led_manager.stop()
        Looper.stop(self)


if __name__ == "__main__":
    # Collect command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--config", required=True, help="Config file with settings for the server")
    args = vars(ap.parse_args())

    config_file = args['config']
    if not os.path.isfile(config_file):
        logger.critical("Cannot find config file: {}".format(config_file))

    with open(config_file) as f:
        text = f.read()

    try:
        config = json.loads(text)
    except:
        logger.critical("Json exception on config file")
        sys.exit()

    server = Server(**config)

    def signal_handler(signal, frame):
        '''Catches control-c and cleanly shuts down the server'''
        logging.info("Control-C caught. Cleanly shutting down the server.")
        server.stop()
        sys.exit()
    signal.signal(signal.SIGINT, signal_handler)
    server.start()
