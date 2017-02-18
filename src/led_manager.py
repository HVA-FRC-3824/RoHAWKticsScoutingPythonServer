from looper import Looper
import RPi.GPIO as GPIO
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

    def __init__(self):
        pass
        #Looper.__init__(self)

        # self.led_status = {self.GREEN: self.NONE, self.YELLOW: self.NONE, self.RED: self.NONE}
        # self.led_pins = {self.GREEN: 40, self.YELLOW: 38, self.RED: 36}
        # self.led_pins = {self.GREEN: 21, self.YELLOW: 20, self.RED: 16}

        # GPIO.setmode(GPIO.BOARD)

        # setup pins
        # GPIO.setup(self.led_pins.values(), GPIO.OUT, initial=GPIO.LOW)

        # self.pstart()
        # self.tstart()

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
        for color, status in self.led_status.items():
            logger.info("color: {} status: {}".format(color, status))
            if status == self.SOLID:
                GPIO.setup(self.led_pins[color], 1)
            elif status == self.NONE:
                GPIO.setup(self.led_pins[color], 0)
            else:
                GPIO.setup(self.led_pins[color], self.iteration % 2)
        self.iteration += 1

        time.sleep(.25)

    def on_pend(self):
        # clean up green and yellow pins, but leave red on if error
        GPIO.setup(self.led_pins[self.GREEN], GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.led_pins[self.YELLOW], GPIO.OUT, initial=GPIO.LOW)

    def on_tend(self):
        # clean up green and yellow pins, but leave red on if error
        GPIO.setup(self.led_pins[self.GREEN], GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.led_pins[self.YELLOW], GPIO.OUT, initial=GPIO.LOW)

    def starting_up(self):
        # self.pipe.send("starting_up")
        # self.set_led(self.GREEN, self.FLASHING)
        pass

    def start_up_complete(self):
        pass
        # GPIO.setup(self.led_pins[self.GREEN], GPIO.OUT, initial=GPIO.HIGH)
        # self.pipe.send("start_up_complete")
        # self.set_led(self.GREEN, self.SOLID)

    def internet_connected(self):
        pass
        # GPIO.setup(self.led_pins[self.YELLOW], GPIO.OUT, initial=GPIO.HIGH)
        # self.pipe.send("internet_connected")
        # self.set_led(self.YELLOW, self.SOLID)

    def internet_connection_down(self):
        pass
        # GPIO.setup(self.led_pins[self.YELLOW], GPIO.OUT, initial=GPIO.LOW)
        # self.pipe.send("internet_connection_down")
        # self.set_led(self.YELLOW, self.NONE)

    def tba_down(self):
        # self.pipe.send("tba_down")
        # self.set_led(self.YELLOW, self.FLASHING)
        pass

    def error(self):
        pass
        # GPIO.setup(self.led_pins[self.RED], GPIO.OUT, initial=GPIO.HIGH)
        # self.pipe.send("error")
        # self.set_led(self.RED, self.SOLID)

    def clear_error(self):
        pass
        # GPIO.setup(self.led_pins[self.RED], GPIO.OUT, initial=GPIO.LOW)
        # self.pipe.send("clear_error")
        # self.set_led(self.RED, self.NONE)

    def set_led(self, color, status):
        pass
        # self.led_status[color] = status
