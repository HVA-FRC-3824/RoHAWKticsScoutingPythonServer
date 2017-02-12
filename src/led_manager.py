from looper import Looper
import RPi.GPIO as GPIO
import time


class LedManager(Looper):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"

    FLASHING = "flashing"
    SOLID = "solid"
    NONE = "none"

    def __init__(self):
        Looper.__init__(self)

        self.led_status = {self.GREEN: self.NONE, self.YELLOW: self.NONE, self.RED: self.NONE}
        self.led_pins = {self.GREEN: 21, self.YELLOW: 20, self.RED: 19}

        GPIO.setmode(GPIO.BOARD)

        # setup pins
        for color, pin in self.led_pins.items():
            GPIO.setup(pin, GPIO.OUT)

        self.pstart()

    def on_pstart(self):
        self.tstart()

    def on_ploop(self, message):
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

    def on_tloop(self):
        for color, status in self.led_status.items():
            if status == self.FLASHING or status == self.SOLID:
                GPIO.output(self.led_pins[color], 1)

        time.sleep(.5)

        for color, status in self.led_status.items():
            if status == self.FLASHING or status == self.NONE:
                GPIO.output(self.led_pins[color], 1)

        time.sleep(.5)

    def on_pend(self):
        # clean up green and yellow pins, but leave red on if error
        GPIO.cleanup(self.led_pins[self.GREEN])
        GPIO.cleanup(self.led_pins[self.YELLOW])

    def starting_up(self):
        self.pipe.send("starting_up")

    def start_up_complete(self):
        self.pipe.send("start_up_complete")

    def internet_connected(self):
        self.pipe.send("internet_connected")

    def internet_connection_down(self):
        self.pipe.send("internet_connection_down")

    def tba_down(self):
        self.pipe.send("tba_down")

    def error(self):
        self.pipe.send("error")

    def clear_error(self):
        self.pipe.send("clear_error")

    def set_led(self, color, status):
        self.led_status[color] = status
