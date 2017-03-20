import socket
import os
import subprocess
import json
import logging
import re

from message_handler import MessageHandler
from socket_connection import SocketConnection

from ourlogging import setup_logging
setup_logging(__file__)
logger = logging.getLogger(__name__)


class RelaySocket:
    shared_state = {}

    def __init__(self):
        # Singleton
        self.__dict__ = self.shared_state

        if not hasattr(self, 'instance'):
            self.port = 38240  # 3824 is taken
            self.setup_adb_bridge()
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind(('', self.port))
            self.server.listen(1)  # Can at most connect to 9 (change the number if you want more)
            self.client = None
            self.message_handler = MessageHandler()
            self.instance = True

    def setup_adb_bridge(self):
        '''Sets up reverse port forward for attached android device running DatabaseRelay via the
           android debug bridge (adb)
        '''
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
        for device in devices:
            logger.info("Reverse port forwarding {0:s}".format(device))
            subprocess.call([self.adb, "-s", device, "reverse", "tcp:{0:d}".format(self.port),
                             "tcp:{0:d}".format(self.port)])

    def wait_for_connection(self):
        (conn, address) = self.server.accept()
        self.client = SocketConnection(conn, self.message_handler)

    def start(self):
        self.client.start()

    def write(self, message):
        if isinstance(message, dict):
            self.write(json.dumps(message))
        elif isinstance(message, str):
            self.client.write(message)
        else:
            logger.error("Unknown type to write")
            raise Exception("Unknown type to write")

    def ping(self):
        data = {"message_type": "ping"}
        self.client.write(json.dumps(data))

    def stop(self):
        self.server.close()
        if hasattr(self, 'client'):
            self.client.stop()
