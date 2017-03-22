import argparse

from database import Database
from the_blue_alliance import TheBlueAlliance
from aggregator import Aggregator


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-e", "--event_key", required=True, help="Event key used by the blue alliance")
    ap.add_argument("-m", "--match", required=True, help="Match number")
    args = vars(ap.parse_args())

    Database(args['event_key'])
    TheBlueAlliance(args['event_key'])

    Aggregator.match_calc(args['match_number'])
    Aggregator.pilot_calc(args['match_number'])
    Aggregator.super_calc()
