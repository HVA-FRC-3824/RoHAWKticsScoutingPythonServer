import logging
# import os
from adb.adb_commands import AdbCommands
# from adb.sign_m2crypto import M2CryptoSigner

from looper import Looper
from ourlogging import setup_logging
setup_logging(__file__)
logger = logging.getLogger(__name__)


class AdbServer(Looper):
    def __init__(self):
        Looper.__init__(self)

        # KitKat+ (4.4+) devices require authentication
        # signer = M2CryptoSigner(os.path.expanduser('~/.android/adbkey'))

        # devices = []
        for device in AdbCommands.Devices():
            print(device)

    def start(self):
        self.tstart()

    def on_tloop(self):
        pass

    def write(self, message):
        pass

# For testing
if __name__ == "__main__":
    adb_server = AdbServer()
