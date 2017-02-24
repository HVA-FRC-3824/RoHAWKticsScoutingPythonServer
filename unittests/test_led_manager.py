import unittest
import ..src.led_manager import LedManager


class LedManagerTest(unittest.TestCase):
    def setUp(self):
        self.led_manager = LedManager()

    def test_starting_up(self):
        self.led_manager.starting_up()

    def test_start_up_complete(self):
        self.led_manager.start_up_complete()

    def test_internet_connected(self):
        self.led_manager.internet_connected()

    def test_internet_connection_down(self):
        self.led_manager.internet_connection_down()

    def test_tba_down(self):
        self.led_manager.tba_down()

    def test_error(self):
        self.led_manager.error()

    def test_clear_error(self):
        self.led_manager.clear_error()


if __name__ == "__main__":
    unittest.main()
