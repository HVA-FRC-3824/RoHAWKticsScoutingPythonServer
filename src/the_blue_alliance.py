import requests
import utils
import logging
import os
import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime as dt
from ourlogging import setup_logging

from data_models.team_ranking_data import TeamRankingData
from tba_models.tba_match import TBAMatch
from tba_models.tba_team import TBATeam
from tba_models.tba_ranking import TBARanking

from database import Database

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


setup_logging(__file__)
logger = logging.getLogger(__name__)


class WebHook(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.end_headers()
        length = int(self.headers['content-length'])
        text = self.rfile.read(length).decode('utf-8')
        d = json.loads(text)
        if d['message_type'] == 'verification':
            logger.info('Verification Key: {}'.format(d['message_data']['verification_key']))
        elif d['message_type'] == 'match_score':
            tba_match = TBAMatch(d['message_data']['match'])
            if tba_match.comp_level == 'qm':
                logger.info('TBA Match {} Received'.format(tba_match.match_number))
                self.tba = TheBlueAlliance()
                if self.tba.event_key == tba_match.event_key:
                    self.tba.update_firebase_match(tba_match)
                    logger.info("Match updated")
                    self.tba.update_firebase_rankings()
                    logger.info("Rankings updated")


class TheBlueAlliance:
    '''Singleton for collecting information from `The Blue Alliance <thebluealliance.com>`_

    Args:
        event_key (`str`): the event id used by `The Blue Alliance <thebluealliance.com>`_
    '''
    shared_state = {}

    def __init__(self, event_key=None, behind_threshold=None):
        self.__dict__ = self.shared_state
        if event_key is not None:
            self.event_key = event_key
            self.base_filepath = os.path.dirname(os.path.abspath(__file__)) + "/../cached/" + self.event_key + "/"
            os.makedirs(self.base_filepath, 0o777, True)

        if behind_threshold is not None:
            self.behind_threshold = behind_threshold

        if not hasattr(self, 'instance'):
            self.instance = True

            self.base_url = "http://www.thebluealliance.com/api/v3/"
            self.headers = {"X-TBA-Auth-Key": "z85XbFohPU0NxV9UWah9lzvQKuGFSZ7vLRWAPAT7V01siaClZGvg1gqi9NG3xef2"}

            self.dt_format = "%a, %d %b %Y %H:%M:%S %Z"

            self.running = True

            if not hasattr(self, 'behind_threshold'):
                self.behind_threshold = 3

    def make_request(self, url):
        '''Send request a url

        Args:
            url (`str`): the url where the data is
        '''
        filepath = url + ".json"

        json_dict = {}
        request_url = "{0:s}event/{1:s}/{2:s}".format(self.base_url, self.event_key, url)

        # check if cached file exists
        if os.path.isfile(self.base_filepath + filepath):
            with open(self.base_filepath + filepath) as f:
                json_dict = json.loads(f.read())

            # if cache has last modified then set the 'if-modified-since' header otherwise remove it
            if 'last_modified' in json_dict:
                self.headers["if-modified-since"] = dt.fromtimestamp(json_dict['last_modified'])\
                    .strftime(self.dt_format)
            elif 'if-modified-since' in self.headers:
                del self.headers['if-modified-since']

            # get request to website
            response = requests.get(request_url, headers=self.headers)

            # 304 means no modifications
            if response.status_code == 304:
                return json_dict['data']
            # 200 is ok, others mean that cached version should be used as there was an error
            elif response.status_code != 200:
                return json_dict['data']

            # header has a 'last-modified' field which is used for caching
            if 'last-modified' in response.headers:
                last_modified = dt.strptime(response.headers['last-modified'], self.dt_format).timestamp()

                # Modifications since cached version
                if json_dict['last_modified'] < last_modified:
                    json_dict['last_modified'] = last_modified
                    json_dict['data'] = json.loads(response.text)
                    with open(self.base_filepath + filepath, 'w') as f:
                        f.write(json.dumps(json_dict, sort_keys=True, indent=4))
                    return json_dict['data']

                # No modifications, so use cached version
                else:
                    return json_dict['data']

            # No 'Last-Modified' field so use data pulled from tba
            else:
                logger.warning("No last-modified header")
                json_dict['data'] = json.loads(response.text)
                with open(self.base_filepath + filepath, 'w') as f:
                    f.write(json.dumps(json_dict, sort_keys=True, indent=4))
                return json_dict['data']

        # no cache file
        else:
            if "if-modified-since" in self.headers:
                del self.headers["if-modified-since"]
            response = requests.get(request_url, headers=self.headers)

            # There should be a last modified header
            if 'last-modified' in response.headers:
                json_dict['last_modified'] = dt.strptime(response.headers['last-modified'], self.dt_format).timestamp()
            else:
                logger.warning("No last-modified header")

            json_dict['data'] = json.loads(response.text)
            with open(self.base_filepath + filepath, 'w') as f:
                f.write(json.dumps(json_dict, sort_keys=True, indent=4))
            return json_dict['data']

    def update_firebase_match(self, tba_match):
        database = Database()
        match = database.get_match(tba_match.match_number)
        match.score_breakdown = tba_match.score_breakdown
        database.set_match(match)

    def get_event_teams(self):
        '''Gets all the team logistic information for an event'''
        logger.info("Downloading teams from The Blue Alliance for {0:s}".format(self.event_key))
        url = "teams"
        data = self.make_request(url)
        teams = []
        for d in data:
            teams.append(TBATeam(d))
        return teams

    def get_event_rankings(self):
        '''Gets all the ranking information for an event'''
        logger.info("Downloading rankings from The Blue Alliance for {0:s}".format(self.event_key))
        url = "rankings"
        data = self.make_request(url)
        rankings = []
        for d in data['rankings']:
            rankings.append(TBARanking(d))
        return rankings

    def update_firebase_rankings(self):
        rankings = self.get_event_rankings()
        database = Database()
        for tba_ranking in rankings:
            ranking = TeamRankingData.from_tba_ranking(tba_ranking)
            database.set_team_ranking_data(ranking, Database.CURRENT)

    def get_event_matches(self):
        '''Gets all the match information for an event'''
        logger.info("Downloading matches from The Blue Alliance for {0:s}".format(self.event_key))
        url = "matches"
        data = self.make_request(url)
        matches = []
        for d in data:
            matches.append(TBAMatch(d))
        return matches

    def is_behind(self, matches):
        '''Checks if `The Blue Alliance <thebluealliance.com>`_ is behind compared to the scouters'''
        completed_matches = len(filter(lambda m: m.comp_level == "qm"
                                       and m.score_breakdown is not None, self.get_event_matches()))
        return abs(len(matches) - completed_matches) >= self.behind_threshold

    def event_down(self):
        '''Checks if `The Blue Alliance <thebluealliance.com>`_ datafeed for this event is down'''
        url = "status"
        if "if-modified-since" in self.headers:
            del self.headers['if-modified-since']
        try:
            response = requests.get(self.base_url + url, headers=self.headers)
        except:
            logger.warning("Caught exception on requesting TBA status")
            return True
        if response.status_code != 200 and response.status_code != 304:
            return True
        data = utils.make_ascii_from_json(response.json())
        return self.event_key in data['down_events'] or data['is_datafeed_down']

    def webhook_handler(self):
        logger.info("TBA Server starting")
        server = HTTPServer(('localhost', 38241), WebHook)
        while self.running:
            server.handle_request()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-e", "--event_key", required=True, help="Event key used by the blue alliance")
    args = vars(ap.parse_args())

    tba = TheBlueAlliance(args['event_key'])
    database = Database(args['event_key'])
    matches = tba.get_event_matches()
    for match in matches:
        if match.comp_level == "qm" and match.score_breakdown is not None:
            logger.info("Getting score breakdown from match {}".format(match.match_number))
            tba.update_firebase_match(match)
    tba.webhook_handler()
