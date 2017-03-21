import json
import time
import logging
from socketserver import StreamRequestHandler
import urlopen

from the_blue_alliance import TheBlueAlliance
from scout_analysis import ScoutAnalysis
from led_manager import LedManager
from aggregator import Aggregator

from ourlogging import setup_logging
setup_logging(__file__)
logger = logging.getLogger(__name__)


class SocketHandler(StreamRequestHandler):

    partial_match_updates = {}
    partial_match_time = {}

    queued_matches = []

    tba = TheBlueAlliance()
    scout_analysis = ScoutAnalysis()
    led_manager = LedManager()

    def handle(self):
        # self.request is the TCP socket connected to the client
        message = self.rfile.readline().strip()
        data = json.loads(message)
        if data['type'] == 'heartbeat':
            self.wfile.write('{"type": "heartbeat", "message": ""}')
        elif data['type'] == 'match':
            match_number = data['message']['match_number']
            team_number = data['message']['team_number']

            if match_number not in self.partial_match_updates:
                self.partial_match_updates[match_number] = []

            if team_number not in self.partial_match_updates[match_number]:
                self.partial_match_updates[match_number].append(team_number)
                self.partial_match_time[match_number] = time.time()

            if len(self.partial_match_updates[match_number]) >= 6:
                del self.partial_match_time[match_number]
                if not self.scout_analysis.analyze(match_number):
                    if self.tba.event_down():
                        try:
                            # try google
                            urlopen('http://216.58.192.142', timeout=1)
                            self.led_manager.tba_down()
                            logger.warning("The Blue Alliance is down (possibly just for this event)")
                            self.messenger.send_message("The Blue Alliance is down (possibly just for this event)")
                        except:
                            self.led_manager.internet_connection_down()
                            logger.warning("Internet connection is down")
                    self.queued_matches.append((match_number, 1))
                else:
                    Aggregator.match_calc(match_number)

        elif data['type'] == 'super':
            Aggregator.super_calc()
        elif data['type'] == 'pilot':
            match_number = data['message']['match_number']
            Aggregator.pilot_calc(match_number)

        # run through queue
        temp = self.queued_matches
        self.queued_matches = []

        for (match_number, attempt) in temp:
            if not self.scout_analysis.analyze(match_number) and attempt < 4:
                if self.tba.event_down():
                    try:
                        urlopen('http://216.58.192.142', timeout=1)
                        self.led_manager.tba_down()
                        logger.warning("The Blue Alliance is down (possibly just for this event)")
                        self.messenger.send_message("The Blue Alliance is down (possibly just for this event)")
                    except:
                        self.led_manager.internet_connection_down()
                        logger.warning("Internet connection is down")
                self.queued_matches.append((match_number, attempt + 1))
            else:
                Aggregator.match_calc(match_number)
