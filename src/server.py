import argparse
import logging
import signal
import os
import sys
import json
import subprocess
import re
import platform

from socketserver import TCPServer, ThreadingMixIn

from the_blue_alliance import TheBlueAlliance
from messenger import Messenger
from led_manager import LedManager
from database import Database
from socket_handler import SocketHandler

from ourlogging import setup_logging

setup_logging(__file__)
logger = logging.getLogger(__name__)


class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    pass


class Server:
    '''Main server class that interprets the config file and starts various threads'''

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
        self.database = Database(self.event_key)
        self.messenger = Messenger(**kwargs)

        self.setup_adb_bridge()

        self.socket_server = ThreadedTCPServer(('localhost', 38240), SocketHandler)

    def setup_adb_bridge(self):
        '''Sets up reverse port forward for attached android device running DatabaseRelay via the
           android debug bridge (adb)
        '''
        if platform.system() == 'Darwin':
            self.adb = '/Users/akmessing1/Library/Android/sdk/platform-tools/adb'
        else:
            self.adb = os.path.dirname(os.path.abspath(__file__)) + "/../adb"
        dir = os.path.dirname(__file__)
        if not os.path.exists(os.path.join(dir, self.adb)):
            logger.error("adb is not compiled")
            raise Exception("adb is not compiled")

        # Grab connected android device serial numbers via adb
        devices_text = subprocess.check_output([self.adb, "devices"], universal_newlines=True)
        pattern = re.compile(r'(.+)\tdevice')
        devices = []
        for line in devices_text.split('\n'):
            matches = pattern.match(line)
            if matches is not None:
                logger.info("Found android device: {}".format(matches.group(matches.lastindex)))
                devices.append(matches.group(matches.lastindex))

        # set reverse port forward for android device running DatabaseRelay
        # device = ''
        port = 38240
        for device in devices:
            logger.info("Reverse port forwarding {0:s}".format(device))
            subprocess.call([self.adb, "-s", device, "reverse", "tcp:{0:d}".format(port),
                             "tcp:{0:d}".format(port)])

    def start(self):
        '''Starts the main thread loop'''
        self.led_manager.start_up_complete()
        self.socket_server.serve_forever()

    def stop(self):
        '''Stops all threads'''
        self.socket_server.shutdown()
        self.socket_server.server_close()
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
