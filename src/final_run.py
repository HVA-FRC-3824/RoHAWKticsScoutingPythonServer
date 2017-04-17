import argparse

from database import Database
from the_blue_alliance import TheBlueAlliance

from aggregator import Aggregator


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-e", "--event_key", required=True, help="Event key used by the blue alliance")
    args = vars(ap.parse_args())

    print("Event key: {}".format(args['event_key']))

    database = Database(args['event_key'])
    tba = TheBlueAlliance(args['event_key'])

    for team in tba.get_event_teams():
        print("Team number: {}".format(team.team_number))
        Aggregator.team_calc(team.team_number)
        Aggregator.team_pilot_calc(team.team_number)
    # print("super")
    # Aggregator.super_calc()
