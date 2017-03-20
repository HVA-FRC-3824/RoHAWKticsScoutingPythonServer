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

from aggregator import Aggregator
from the_blue_alliance import TheBlueAlliance
from scout_analysis import ScoutAnalysis
from messenger import Messenger
from message_handler import MessageHandler
from led_manager import LedManager
from relay_socket import RelaySocket

from ourlogging import setup_logging

setup_logging(__file__)
logger = logging.getLogger(__name__)


class Server:
    '''Main server class that interprets the config file and starts various threads'''

    PING_TIMEOUT = 5  # 5 seconds
    HEARTBEAT_TIME = 60 * 30  # 30 minutes
    LOOP_TIME = 60 * 10  # 10 minutes

    def __init__(self, **kwargs):
        ''' Initialization of all the server components based on the config

        Kwargs:
            The config json converted to a `dict`
        '''
        self.event_key = kwargs.get('event_key', "")
        if self.event_key == "":
            logger.critical("No event key")
            sys.exit()
        logger.info("Event Key: {0:s}".format(self.event_key))

        self.led_manager = LedManager()
        self.led_manager.starting_up()

        self.tba = TheBlueAlliance(self.event_key)

        # event for threading not FIRST event
        self.event = None

        self.messenger = Messenger(**kwargs)

        self.message_handler = MessageHandler()

        self.socket = RelaySocket()

        if kwargs.get('scout_analysis', False):
            self.scout_analysis = ScoutAnalysis(**kwargs)

    def start(self):
        '''Starts the main thread loop'''
        self.socket.wait_for_connection()
        self.socket.start()
        self.led_manager.start_up_complete()
        self.event = None
        self.running = True
        iteration = 1
        last_heartbeat = None
        while self.running:
            start_time = time.time()
            # Heartbeat
            if last_heartbeat is None or time.time() > last_heartbeat + self.HEARTBEAT_TIME:
                # Check Internet connection
                if self.tba.event_down():
                    try:
                        urlopen('http://216.58.192.142', timeout=1)
                        self.led_manager.tba_down()
                        logger.warning("The Blue Alliance is down (possibly just for this event)")
                        self.messenger.send_message("The Blue Alliance is down (possibly just for this event)")
                    except:
                        self.led_manager.internet_connection_down()
                        logger.warning("Internet connection is down")

                # Ping phone
                self.message_handler.pong = False
                self.socket.ping()
                ping_start = time.time()
                while not self.message_handler.pong and time.time() - ping_start < self.PING_TIMEOUT:
                    pass
                if not self.message_handler.pong:
                    self.led_manager.error()
                    logger.error("Heartbeat error: No pong received")
                last_heartbeat = time.time()

            while self.message_handler.updates_available():
                update = self.message_handler.get_next_update()
                self.handle_update(update)

            # Alert admin if there are any matches that have timed out waiting on all tmds to come in
            # Probably means someone didn't hit save
            for match_number, team_number_list in self.message_handler.get_partial_matches_timeout():
                self.messenger.send_message("Match {} missing tmd".format(match_number),
                                            "Teams received {}".format(team_number_list))

            end_time = time.time()
            iteration += 1
            if self.running and end_time - start_time < self.LOOP_TIME:
                # Event is used, so that we can stop the loop early if quitting
                self.event = Event()
                self.event.wait(timeout=self.LOOP_TIME - (end_time - start_time))
                self.event = None

    def handle_update(self, update):
        if update['update_type'] == 'match':
            # scout analysis failure mean tba hasn't been updated with this match
            # After 3 we assume something is up with tba
            if not self.scout_analysis.analyze(update['match_number']) and update['update_attempt'] < 3:
                if self.tba.is_down():
                    update['update_attempt'] += 1
                    self.message_handler.updates_queue.append(update)
                elif self.tba.is_behind():
                    update['update_attempt'] += 1
                    self.message_handler.updates_queue.append(update)
                else:
                    update['update_attempt'] += 1
                    self.message_handler.updates_queue.append(update)

            Aggregator.match_calc(update['match_number'])
        elif update['update_type'] == 'super':
            Aggregator.super_calc()
        elif update['update_type'] == 'pilot':
            Aggregator.pilot_calc(update['match_number'])
        else:
            logger.error("Unknown update type")

    def stop(self):
        '''Stops all threads'''
        self.running = False
        self.socket.stop()
        if self.event is not None:
            self.event.set()
        self.led_manager.stop()


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
