import argparse

from database import Database
from the_blue_alliance import TheBlueAlliance
from aggregator import Aggregator


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-e", "--event_key", required=True, help="Event key used by the blue alliance")
    ap.add_argument("-m", "--match_number", required=True, help="Match number")
    args = vars(ap.parse_args())

    database = Database(args['event_key'])
    TheBlueAlliance(args['event_key'])

    match = database.get_match(args['match_number'])
    for team_number in match.team_numbers:
        Aggregator.team_calc(team_number)
    Aggregator.pilot_calc(args['match_number'])
    Aggregator.super_calc()
