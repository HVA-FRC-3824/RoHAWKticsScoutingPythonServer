import argparse

from database import Database
from the_blue_alliance import TheBlueAlliance
from aggregator import Aggregator


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-e", "--event_key", required=True, help="Event key used by the blue alliance")
    ap.add_argument("-n", "--num_matches", required=True, help="Number of completed matches")
    args = vars(ap.parse_args())

    Database(args['event_key'])
    TheBlueAlliance(args['event_key'])

    for match_number in range(args['num_matches']):
        Aggregator.match_calc(match_number)
        Aggregator.pilot_calc(match_number)
        Aggregator.super_calc()
