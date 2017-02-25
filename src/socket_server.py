import hashlib
import logging
import socket
import time
import select
import subprocess
import os
import re
import usb1

from message_handler import MessageHandler
from looper import Looper
from ourlogging import setup_logging
setup_logging(__file__)
logger = logging.getLogger(__name__)


class SocketConnection(Looper):
    '''A single socket connection for reading and writing'''
    HEADER_MSB = 0x10
    HEADER_LSB = 0x55
    RECEIVING = 0
    SENDING = 1

    def __init__(self, conn, message_handler):
        '''
        Args:
            conn (:class:`Connection`):
            message_handler (:class:`MessageHandler`)
        '''
        Looper.__init__(self)
        self.state = self.RECEIVING
        self.socket = conn
        self.message_handler = message_handler
        logger.debug("Socket client created")

    def start(self):
        '''Starts the receiving loop'''
        self.tstart()

    def on_tloop(self):
        '''Recieves messages from an android tablet'''
        socket_list = [self.socket]
        read_list, write_list, error_list = select.select(socket_list, [], [])
        if self.socket in read_list and self.state == self.RECEIVING:
            waiting_for_header = True
            header_bytes = bytearray([0]*22)
            digest = bytearray([0]*16)
            header_index = 0

            while self.running:
                if waiting_for_header:
                    header = self.socket.recv(1)
                    if len(header) == 0:
                        # closing hack
                        self.running = False
                        return
                    header_bytes[header_index] = header[0]
                    header_index += 1

                    if header_index == 22:
                        if header_bytes[0] == self.HEADER_MSB and header_bytes[1] == self.HEADER_LSB:
                            total_size = self.bytearray_to_int(header_bytes[2:6])
                            digest = header_bytes[6:22]
                            waiting_for_header = False
                        else:
                            logger.error("Received message does not have correct header")
                            break
                else:
                    buf = self.socket.recv(total_size)
                    if self.digest_match(self.get_digest(buf), digest):
                        self.socket.send(digest)
                        logger.info("Received message: {0:s}".format(buf.decode()))
                        reply = self.message_handler.handle_message(buf.decode())
                        if reply is not None:
                            self.write(reply)
                        break
                    else:
                        logger.error("Received message digest does not match")
        read_list, write_list, error_list = select.select(socket_list, [], [])
        while self.socket not in read_list and self.state != self.RECEIVING and self.running:
            time.sleep(0.1)
            read_list, write_list, error_list = select.select(socket_list, [], [])

    def write(self, message):
        '''Writes a message to the android tablet

        Args:
            message (str): message to send to the tablet

        Returns:
            bool. Whether the message was successfully sent
        '''
        logger.info("SCT writing {}".format(message))
        try:
            self.socket.write(self.HEADER_MSB)
            self.socket.write(self.HEADER_LSB)

            message_len = self.int_to_bytearray(len(message))
            self.write(message_len)

            message_bytes = bytearray(message)

            self.write(message_bytes)
            self.flush()
            digest = self.get_digest(message_bytes)

            incoming_digest = [0]*16
            incoming_digest = bytearray(incoming_digest)
            incoming_index = 0

            while True:
                header = self.bluetooth.recv(1)
                if header is None or len(header) == 0:
                    logger.error("Acknowledgement not received")
                    return False
                incoming_digest[incoming_index] = header
                incoming_index += 1
                if incoming_index == 16:
                    if self.digest_match(digest, incoming_digest):
                        return True
                    else:
                        logger.error("Written message digest does not match")
                        return False
        except:
            logger.error("TimeoutExcpetion on write")
            return False

    def bytearray_to_int(self, b):
        '''Converts a `bytearray` to `int`'''
        return (b[3] & 0xFF) + ((b[2] & 0xFF) << 8) + ((b[1] & 0xFF) << 16) + ((b[0] & 0xFF) << 24)

    def int_to_bytearray(self, a):
        '''Converst an `int` to `bytearray`'''
        ret = bytearray([0]*4)
        ret[3] = a & 0xFF
        ret[2] = (a >> 8) & 0xFF
        ret[1] = (a >> 16) & 0xFF
        ret[0] = (a >> 24) & 0xFF
        return ret

    def get_digest(self, message_bytes):
        '''Returns the digest of the message

        Args:
            message_bytes (bytes): the message

        Returns:
            the digest of the message
        '''
        m = hashlib.md5()
        m.update(message_bytes)
        return m.digest()

    def digest_match(self, digest1, digest2):
        '''Checks if two digests matches

        Args:
            digest1: The first digest to compare

            digest2: The second digest to compare

        Returns:
            bool. Whether the digest matches
        '''
        if len(digest1) != len(digest2):
            return False
        for i in range(len(digest1)):
            if digest1[i] != digest2[i]:
                return False
        return True


class SocketServer(Looper):
    '''The server for socket connections with the android tablets'''
    # Singleton
    shared_state = {}

    ANDROID_VENDOR_IDS = ["0x18d1"]
    ANDROID_PRODUCT_IDS = ["0x4ee2"]

    def __init__(self):
        '''Initializes the singleton or provides the already created one'''
        self.__dict__ = self.shared_state
        if not hasattr(self, 'instance'):
            Looper.__init__(self)
            self.port = 38240  # 3824 is taken
            self.setup_adb_bridge()
            self.pstart()
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind(('', self.port))
            self.server.listen(9)  # Can at most connect to 9 (change the number if you want more)
            self.server.settimeout(5)

            self.clients = []

            self.message_handler = MessageHandler()
            self.instance = True

    def setup_adb_bridge(self):
        '''Sets up reverse port forward for attached android devices via the
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

        # set reverse port forward for each android device
        for device in devices:
            logger.info("Reverse port forwarding {0:s}".format(device))
            subprocess.call([self.adb, "-s", device, "reverse", "tcp:{0:d}".format(self.port),
                             "tcp:{0:d}".format(self.port)])

    def on_pstart(self):
        '''Sets up the :func:`hotplug_callback` to trigger when a usb device is
           plugged in
        '''
        logger.info("hotplug process started")
        self.context = usb1.USBContext().__enter__()
        self.context.hotplugRegisterCallback(self.hotplug_callback)

    def on_ploop(self, message=""):
        '''Checks for the hotplug event'''
        self.context.handleEvents()

    def hotplug_callback(self, context, device, event):
        '''Checks if the plugged in device is a nexus tablet and if so starts
           reverse port forwarding via adb
        '''
        if event == usb1.HOTPLUG_EVENT_DEVICE_ARRIVED:
            logger.info("Devices {0:s}:{1:s} plugged in".format(hex(device.getVendorID()),
                                                                hex(device.getProductID())))
            if(hex(device.getVendorID()) in self.ANDROID_VENDOR_IDS and
               hex(device.getProductID()) in self.ANDROID_PRODUCT_IDS):
                logger.info("Reverse port forwarding on {0:s}".format(device.getSerialNumber()))
                # Delay so adb can find the device
                time.sleep(1)
                subprocess.call([self.adb, "-s", device.getSerialNumber(), "reverse",
                                 "tcp:{0:d}".format(self.port), "tcp:{0:d}".format(self.port)])

    def start(self):
        '''Starts the thread for accepting socket connections'''
        self.tstart()

    def on_tstart(self):
        '''Marks that the thread has started'''
        logger.debug("Socket Accept Thread started")

    def on_tloop(self):
        '''Listens for a connect from one of the android tablets and spins off
           a thread to handle it
        '''
        try:
            (conn, address) = self.server.accept()
            self.clients.append(SocketConnection(conn, self.message_handler))
            self.clients[-1].start()
        except:
            pass

    def stop(self):
        '''Stops each connection thread and the main accepting thread'''
        self.server.close()
        for client in self.clients:
            client.stop()
        self.server.close()
        Looper.stop(self)
