import requests
import utils
import logging
import os
import json
from ourlogging import setup_logging

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


setup_logging(__file__)
logger = logging.getLogger(__name__)


class TheBlueAlliance:
    '''Singleton for collecting information from `The Blue Alliance <thebluealliance.com>`_

    Args:
        event_id (`str`): the event id used by `The Blue Alliance <thebluealliance.com>`_
    '''
    shared_state = {}

    def __init__(self, event_id=None, behind_threshold=None):
        self.__dict__ = self.shared_state
        if event_id is not None:
            self.event_id = event_id
            self.base_filepath = os.path.dirname(os.path.abspath(__file__)) + "/../cached/" + self.event_id + "/"

        if behind_threshold is not None:
            self.behind_threshold = behind_threshold

        if not hasattr(self, 'instance'):
            self.base_url = "http://www.thebluealliance.com/api/v2/"
            self.header_key = "X-TBA-App-Id"
            self.header_value = "frc3824:scouting-system:v1"

            if not hasattr(self, 'behind_threshold'):
                self.behind_threshold = 3

            self.instance = True

    def setup_folders(self):
        for ext in ["teams", "matches", "rankings"]:
            os.mkdirs(self.base_filepath + ext)

    def make_request(self, url, filepath):
        '''Send request a url

        Args:
            url (`str`): the url where the data is
        '''

        if os.path.isfile(self.base_filepath + filepath):
            with open(self.base_filepath + filepath) as f:
                json_dict = json.loads(f.read())
            response = requests.get(self.base_url + url,
                                    headers={self.header_key: self.header_value,
                                             "If-Modified-Since": json_dict['last_modified']})
            if json_dict['last_modified'] < response.headers['Last-Modified']:
                json_dict['last_modified'] = response.headers['Last-Modified']
                json_dict['data'] = utils.make_ascii_from_json(response.json())
                with open(self.base_filepath + filepath, 'w') as f:
                    f.write(json.dumps(json_dict))
                return json_dict['data']
            else:
                return json_dict['data']

        else:
            json_dict = {}
            json_dict['last_modified'] = response.headers['Last-Modified']
            json_dict['data'] = utils.make_ascii_from_json(response.json())
            with open(self.base_filepath + filepath, 'w') as f:
                f.write(json.dumps(json_dict))
            return json_dict['data']

    def get_event_teams(self):
        '''Gets all the team logistic information for an event'''
        logger.info("Downloading teams from The Blue Alliance for {0:s}".format(self.event_id))
        url = ("event/{0:s}/teams").format(self.event_id)
        filepath = "{0:s}/teams.json".format(self.event_id)
        data = self.make_request(url, filepath)
        return data

    def get_event_rankings(self):
        '''Gets all the ranking information for an event'''
        logger.info("Downloading rankings from The Blue Alliance for {0:s}".format(self.event_id))
        url = ("event/{0:s}/rankings").format(self.basic_url, self.event_id)
        filepath = "{0:s}/rankings.json".format(self.event_id)
        data = self.make_request(url, filepath)
        return data

    def get_event_matches(self):
        '''Gets all the match information for an event'''
        logger.info("Downloading matches from The Blue Alliance for {0:s}".format(self.event_id))
        url = ("event/{0:s}/matches").format(self.basic_url, self.event_id)
        filepath = "{0:s}/matches.json".format(self.event_id)
        data = self.make_request(url, filepath)
        return data

    def is_behind(self, matches):
        '''Checks if `The Blue Alliance <thebluealliance.com>`_ is behind compared to the scouters'''
        completed_matches = len(filter(lambda m: m['comp_level'] == "qm"
                                       and m['score_breakdown'] is not None, self.get_event_matches()))
        return abs(len(matches) - completed_matches) >= self.behind_threshold

    def event_down(self):
        '''Checks if `The Blue Alliance <thebluealliance.com>`_ datafeed for this event is down'''
        url = "{0:s}/status".format(self.base_url)
        data = utils.make_ascii_from_json(requests.get(self.base_url + url,
                                                       headers={self.header_key: self.header_value}).json())
        return self.event_id in data['down_events'] or data['is_datafeed_down']
