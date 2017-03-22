import unittest
from ..src.the_blue_alliance import TheBlueAlliance


class TBATests(unittest.TestCase):
    '''Tests for `the_blue_alliance.py`'''

    def setUp(self):
        self.tba = TheBlueAlliance("2016tnkn")

    def test_get_event_teams(self):
        event_teams = self.tba.get_event_teams()
        self.assertEqual(len(event_teams) == 49)

    def test_get_event_matches(self):
        event_matches = self.tba.get_event_matches()
        self.assertEqual(len(event_matches) == 82 + 14)

    def test_get_event_rankings(self):
        event_rankings = self.tba.get_event_rankings()
        self.assertEqual(len(event_rankings), 49)

    def test_is_behind(self):
        is_behind = self.tba.is_behind(82)
        self.assertFalse(is_behind)

    def test_event_down(self):
        event_down = self.tba.event_down()
        self.assertFalse(event_down)


if __name__ == "__main__":
    unittest.main()
