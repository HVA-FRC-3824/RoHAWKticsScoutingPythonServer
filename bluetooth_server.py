import serial
import md5

from looper import Looper


class BluetoothServer(Looper):
    HEADER_MSB = 0x10
    HEADER_LSB = 0x55
    RECEIVING = 0
    SENDING = 1

    def __init__(self):
        self.bluetooth = serial.Serial("/dev/rfcomm1", baudrate=9600)
        self.state = self.RECEIVING

    def on_tloop(self):
        while self.running:
            if self.bluetooth.in_waiting > 0 and self.state == self.RECEIVING:
                waiting_for_header = True
                header_bytes = bytearray([0]*22)
                digest = bytearray([0]*16)
                header_index = 0

                while self.running:
                    if waiting_for_header:
                        header = self.bluetooth.read()
                        header_bytes[header_index] = header
                        header_index += 1

                        if header_index == 22:
                            if header_bytes[0] == self.HEADER_MSB and header_bytes[1] == self.HEADER_LSB:
                                total_size = self.byte_array_to_int(header_bytes[2:6])
                                digest = header_bytes[6:22]
                                waiting_for_header = False
                            else:
                                # error
                                break
                    else:
                        buffer = self.bluetooth.read(total_size)
                        if self.digest_match(self.get_digest(buffer), digest):
                            # Receive handler
                            self.bluetooth.write(digest)
                        else:
                            # error
                            pass
            while self.bluetooth.in_waiting > 0 and self.state != self.RECEIVING and self.running:
                pass

    def write(self, message):
        try:
            self.bluetooth.write(self.HEADER_MSB)
            self.bluetooth.write(self.HEADER_LSB)

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
                header = self.bluetooth.read()
                if header is None or len(header) == 0:
                    return False
                incoming_digest[incoming_index] = header
                incoming_index += 1
                if incoming_index == 16:
                    if self.digest_match(digest, incoming_digest):
                        return True
                    else:
                        return False
        except serial.SerialTimeoutException:
            return False

    def bytearray_to_int(self, b):
        return (b[3] & 0xFF) + ((b[2] & 0xFF) << 8) + ((b[1] & 0xFF) << 16) + ((b[0] & 0xFF) << 24)

    def int_to_bytearray(self, a):
        ret = bytearray([0]*4)
        ret[3] = a & 0xFF
        ret[2] = (a >> 8) & 0xFF
        ret[1] = (a >> 16) & 0xFF
        ret[0] = (a >> 24) & 0xFF
        return ret

    def get_digest(self, message_bytes):
        m = md5.new()
        m.update(message_bytes)
        return m.digest

    def digest_match(self, digest1, digest2):
        if len(digest1) != len(digest2):
            return False
        for i in range(len(digest1)):
            if digest1[i] != digest2[i]:
                return False
        return True
