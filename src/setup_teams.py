import argparse
from the_blue_alliance import TheBlueAlliance
from database import Database
from data_models.team_logistics import TeamLogistics
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

    teams = tba.get_event_teams()

    for team in teams:
        d = {'team_number': team.team_number, 'nickname': team.nickname}
        t = TeamLogistics(d)
        logger.info("Adding team {}".format(team.team_number))
        database.set_team_logistics(t)