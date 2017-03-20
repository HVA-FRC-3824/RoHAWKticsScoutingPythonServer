import argparse
from the_blue_alliance import TheBlueAlliance
from database import Database
from data_models.match import Match
import logging
from ourlogging import setup_logging
setup_logging(__file__)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    # Collect command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-e", "--event_key", required=True, help="Event key used by the blue alliance")
    args = vars(ap.parse_args())

    tba = TheBlueAlliance(args['event_key'])
    database = Database(args['event_key'])

    matches = tba.get_event_matches()

    team_matches = {}
    team_surrogate_matches = {}

    for match in matches:
        team_numbers = []
        for team_key in match.alliances.blue.team_keys:
            team_number = int(team_key[3:])
            team_numbers.append(team_number)
            if team_number not in team_matches:
                team_matches[team_number] = []
            team_matches[team_number].append(match.match_number)
            if team_key in match.alliances.blue.surrogate_team_keys:
                team_surrogate_matches[team_number] = match.match_number

        for team_key in match.alliances.red.team_keys:
            team_number = int(team_key[3:])
            team_numbers.append(team_number)
            if team_number not in team_matches:
                team_matches[team_number] = []
            team_matches[team_number].append(match.match_number)
            if team_key in match.alliances.red.surrogate_team_keys:
                team_surrogate_matches[team_number] = match.match_number

        d = {'match_number': match.match_number, 'team_numbers': team_numbers}

        m = Match(d)
        logger.info("Adding match {}".format(match.match_number))
        database.set_match(m)

    for team_number, team_match_list in team_matches.items():
        t = database.get_team_logistics(team_number=team_number)
        t.match_numbers = team_match_list
        if team_number in team_surrogate_matches:
            t.surrogate_match_number = team_surrogate_matches[team_number]
        database.set_team_logistics(t)
        logger.info("Updated team {}".format(team_number))
