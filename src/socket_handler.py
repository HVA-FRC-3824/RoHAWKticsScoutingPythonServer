import json
# import time
import logging
from socketserver import StreamRequestHandler
# from urllib.request import urlopen

from the_blue_alliance import TheBlueAlliance
# from scout_analysis import ScoutAnalysis
from led_manager import LedManager
from aggregator import Aggregator

from ourlogging import setup_logging
setup_logging(__file__)
logger = logging.getLogger(__name__)


class SocketHandler(StreamRequestHandler):
    tba = TheBlueAlliance()
    # scout_analysis = ScoutAnalysis()
    led_manager = LedManager()

    def handle(self):
        logger.info("New client: {}".format(self.client_address[0]))
        for line in self.rfile:
            message = str(line, 'utf-8').strip()
            logger.info("Message Received: {}".format(message))
            try:
                data = json.loads(message)
            except:
                logger.warning("{} not jsonable".format(message))
                continue

            # Received heartbeat. Respond with heartbeat
            if data['type'] == 'heartbeat':
                response = {}
                response['type'] = "heartbeat"
                response['data'] = {}

                response_text = json.dumps(response) + "\n"
                logger.info("Response: {}".format(response_text))
                self.wfile.write(response_text.encode('utf-8'))

            # Team Match Data Update
            elif data['type'] == 'match':
                match_number = data['data']['match_number']
                Aggregator.match_calc(match_number)
                Aggregator.pilot_calc(match_number)

                response = {}
                response['type'] = 'match'
                response['data'] = {'match_number': match_number}
                response_text = json.dumps(response) + "\n"
                logger.info("Response: {}".format(response_text))
                self.wfile.write(response_text.encode('utf-8'))

            elif data['type'] == 'team':
                team_number = data['data']['team_number']
                Aggregator.team_calc(team_number)
                Aggregator.pilot_team_calc(team_number)

                response = {}
                response['type'] = 'team'
                response['data'] = {'team_number': team_number}
                response_text = json.dumps(response) + "\n"
                logger.info("Response: {}".format(response_text))
                self.wfile.write(response_text.encode('utf-8'))
            # Super Match Data Update
            elif data['type'] == 'super':
                # Aggregate super match data
                Aggregator.super_calc()

                response = {}
                response['type'] = 'super'
                response['data'] = {}
                response_text = json.dumps(response) + "\n"
                logger.info("Response: {}".format(response_text))
                self.wfile.write(response_text.encode('utf-8'))

            elif data['type'] == 'final_run':
                for team in self.tba.get_event_teams():
                    print("Team number: {}".format(team.team_number))
                    Aggregator.team_calc(team.team_number)
                    Aggregator.pilot_team_calc(team.team_number)

                print("super")
                Aggregator.super_calc()

                response = {}
                response['type'] = 'final_run'
                response['data'] = {}
                response_text = json.dumps(response) + "\n"
                logger.info("Response: {}".format(response_text))
                self.wfile.write(response_text.encode('utf-8'))

        logger.info("Client lost: {}".format(self.client_address[0]))
