from the_blue_alliance import TheBlueAlliance
from database import Database
from aggregator import Aggregator
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("-e", "--event_key", required=True, help="Event key used by the blue alliance")
args = vars(ap.parse_args())


Database(args['event_key'])
TheBlueAlliance(args['event_key'])

Aggregator.pilot_calc(1)
