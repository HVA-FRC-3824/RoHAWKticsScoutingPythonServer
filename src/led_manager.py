from looper import Looper
try:
    import RPi.GPIO as GPIO
except:
    GPIO = None
import time
import logging

from ourlogging import setup_logging
setup_logging(__file__)
logger = logging.getLogger(__name__)


class LedManager(Looper):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"

    FLASHING = "flashing"
    SOLID = "solid"
    NONE = "none"

    shared_state = {}

    def __init__(self):
        self.__dict__ = self.shared_state

        if not hasattr(self, 'instance'):
            Looper.__init__(self)

            self.led_status = {self.GREEN: self.NONE, self.YELLOW: self.NONE, self.RED: self.NONE}
            self.led_pins = {self.GREEN: 40, self.YELLOW: 38, self.RED: 36}
            if GPIO is not None:
                GPIO.setwarnings(False)
                GPIO.setmode(GPIO.BOARD)

                # setup pins
                GPIO.setup(list(self.led_pins.values()), GPIO.OUT, initial=GPIO.LOW)

            self.pstart()
            self.instance = True

    def on_pstart(self):
        self.tstart()

    def on_ploop(self, message):
        logger.info(message)
        if message == "starting_up":
            self.set_led(self.GREEN, self.FLASHING)
        elif message == "start_up_complete":
            self.set_led(self.GREEN, self.SOLID)
        elif message == "internet_connected":
            self.set_led(self.YELLOW, self.SOLID)
        elif message == "internet_connection_down":
            self.set_led(self.YELLOW, self.NONE)
        elif message == "tba_down":
            self.set_led(self.YELLOW, self.FLASHING)
        elif message == "error":
            self.set_led(self.RED, self.SOLID)
        elif message == "clear_error":
            self.set_led(self.RED, self.NONE)

    def on_tstart(self):
        self.iteration = 0

    def on_tloop(self):
        if GPIO is not None:
            for color, status in self.led_status.items():
                # logger.info("color: {} status: {}".format(color, status))
                if status == self.SOLID:
                    GPIO.output(self.led_pins[color], 1)
                elif status == self.NONE:
                    GPIO.output(self.led_pins[color], 0)
                else:
                    GPIO.output(self.led_pins[color], self.iteration % 2)
        self.iteration += 1

        time.sleep(.25)

    def on_pend(self):
        if GPIO is not None:
            # clean up green and yellow pins, but leave red on if error
            GPIO.output(self.led_pins[self.GREEN], 0)
            GPIO.output(self.led_pins[self.YELLOW], 0)

    def on_tend(self):
        if GPIO is not None:
            # clean up green and yellow pins, but leave red on if error
            GPIO.output(self.led_pins[self.GREEN], 0)
            GPIO.output(self.led_pins[self.YELLOW], 0)

    def starting_up(self):
        self.pipe.send("starting_up")
        # self.set_led(self.GREEN, self.FLASHING)

    def start_up_complete(self):
        self.pipe.send("start_up_complete")
        # self.set_led(self.GREEN, self.SOLID)

    def internet_connected(self):
        self.pipe.send("internet_connected")
        # self.set_led(self.YELLOW, self.SOLID)

    def internet_connection_down(self):
        self.pipe.send("internet_connection_down")
        # self.set_led(self.YELLOW, self.NONE)

    def tba_down(self):
        self.pipe.send("tba_down")
        # self.set_led(self.YELLOW, self.FLASHING)

    def error(self):
        self.pipe.send("error")
        # self.set_led(self.RED, self.SOLID)

    def clear_error(self):
        self.pipe.send("clear_error")
        # self.set_led(self.RED, self.NONE)

    def set_led(self, color, status):
        self.led_status[color] = status
