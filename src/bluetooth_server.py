import hashlib
import logging
import time
import select
from bluetooth.bluez import BluetoothSocket, discover_devices

from message_handler import MessageHandler
from looper import Looper
from ourlogging import setup_logging
setup_logging(__file__)
logger = logging.getLogger(__name__)


class BluetoothConnection(Looper):
    '''A bluetooth socket connection for reading and writing'''
    HEADER_MSB = 0x10
    HEADER_LSB = 0x55
    RECEIVING = 0
    SENDING = 1

    def __init__(self, conn, address, message_handler):
        Looper.__init__(self)
        self.state = self.RECEIVING
        self.address = address
        self.bluetooth = conn
        self.message_handler = message_handler

    def start(self):
        '''Starts the receiving loop'''
        self.tstart()

    def on_tstart(self):
        '''Marks the start of the bluetooth connection thread'''
        logger.debug("BTC {} thread started".format(self.address))

    def on_tloop(self):
        '''Recieves messages from an android tablet'''
        socket_list = [self.bluetooth._sock]
        read_list, write_list, error_list = select.select(socket_list, [], [])
        if self.bluetooth._sock in read_list and self.state == self.RECEIVING:
            waiting_for_header = True
            header_bytes = bytearray([0]*22)
            digest = bytearray([0]*16)
            header_index = 0

            while self.running:
                if waiting_for_header:
                    try:
                        header = self.bluetooth.recv(1)
                        if len(header) == 0:
                            # closing hack
                            self.running = False
                            return
                    except:
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
                    buf = self.bluetooth.recv(total_size)
                    if self.digest_match(self.get_digest(buf), digest):
                        self.bluetooth.send(bytes(digest))
                        logger.info("Received message: {0:s}".format(buf.decode()))
                        reply = self.message_handler.handle_message(buf.decode())
                        if reply is not None:
                            self.write(reply)
                        break
                    else:
                        logger.error("Received message digest does not match")
        read_list, write_list, error_list = select.select(socket_list, [], [])
        while self.bluetooth._sock in read_list and self.state != self.RECEIVING and self.running:
            time.sleep(0.1)
            read_list, write_list, error_list = select.select(socket_list, [], [])

    def write(self, message):
        '''Writes a message to the android tablet

        Args:
            message (str): message to send to the tablet

        Returns:
            bool. Whether the message was successfully sent
        '''
        logger.info("BTC writing {}".format(message))
        try:
            self.bluetooth.send(self.HEADER_MSB)
            self.bluetooth.send(self.HEADER_LSB)

            message_len = self.int_to_bytearray(len(message))
            self.write(message_len)

            message_bytes = bytearray(message)

            self.bluetooth.send(message_bytes)
            self.bluetooth.flush()
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
            logger.error("SerialTimeoutExcpetion on write")
        except:
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


class BluetoothServer(Looper):
    '''The server for bluetooth connections with the android tablets'''
    # Singleton
    shared_state = {}

    def __init__(self):
        '''Initializes the singleton or provides the already created one'''
        self.__dict__ = self.shared_state
        if not hasattr(self, 'instance'):
            Looper.__init__(self)
            nearby_devices = discover_devices(lookup_names=True)
            for addr, name in nearby_devices:
                logger.info("BT: %s - %s" % (addr, name))

            self.bluetooth = BluetoothSocket()  # defaults to RF_COMM
            self.bluetooth.bind(("", 0))  # PORT_ANY = 0
            self.bluetooth.listen(9)
            self.bluetooth.settimeout(5)
            self.clients = []

            self.message_handler = MessageHandler()
            self.instance = True

    def start(self):
        '''Starts the thread for accepting bluetooth connections'''
        self.tstart()

    def on_tstart(self):
        '''Marks that the thread has started'''
        logger.debug("Bluetooth accept thread started")

    def on_tloop(self):
        '''Listens for a connect from one of the android tablets and spins off
           a thread to handle it
        '''
        try:
            (conn, address) = self.bluetooth.accept()
            logger.info("New connection accepted: {}".format(address))
            self.clients.append(BluetoothConnection(conn, address, self.message_handler))
            self.clients[-1].start()
        except:
            pass

    def stop(self):
        '''Stops each connection thread and the main accepting thread'''
        for client in self.clients:
            client.stop()
        Looper.stop(self)
