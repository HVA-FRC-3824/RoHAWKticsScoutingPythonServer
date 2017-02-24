import requests
import utils
import logging
import os
import json
from datetime import datetime as dt
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
            os.makedirs(self.base_filepath, 0o777, True)

        if behind_threshold is not None:
            self.behind_threshold = behind_threshold

        if not hasattr(self, 'instance'):
            self.base_url = "http://www.thebluealliance.com/api/v3/"
            self.headers = {"X-TBA-Auth-Key": "T17kbsiAc8dNL9EGuxIN9EyjP2XCJKVeN5hg5ILqxYF6CW1MFm0WehgsRsicdRYW"}

            self.dt_format = "%a, %d %b %Y %H:%M:%S %Z"

            if not hasattr(self, 'behind_threshold'):
                self.behind_threshold = 3

            self.instance = True

    def make_request(self, url):
        '''Send request a url

        Args:
            url (`str`): the url where the data is
        '''
        filepath = url + ".json"

        json_dict = {}
        request_url = "{0:s}event/{1:s}/{2:s}".format(self.base_url, self.event_id, url)
        print(request_url)

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

    def get_event_teams(self):
        '''Gets all the team logistic information for an event'''
        logger.info("Downloading teams from The Blue Alliance for {0:s}".format(self.event_id))
        url = "teams"
        data = self.make_request(url)
        return data

    def get_event_rankings(self):
        '''Gets all the ranking information for an event'''
        logger.info("Downloading rankings from The Blue Alliance for {0:s}".format(self.event_id))
        url = "rankings"
        data = self.make_request(url)
        return data

    def get_event_matches(self):
        '''Gets all the match information for an event'''
        logger.info("Downloading matches from The Blue Alliance for {0:s}".format(self.event_id))
        url = "matches"
        data = self.make_request(url)
        return data

    def is_behind(self, matches):
        '''Checks if `The Blue Alliance <thebluealliance.com>`_ is behind compared to the scouters'''
        completed_matches = len(filter(lambda m: m['comp_level'] == "qm"
                                       and m['score_breakdown'] is not None, self.get_event_matches()))
        return abs(len(matches) - completed_matches) >= self.behind_threshold

    def event_down(self):
        '''Checks if `The Blue Alliance <thebluealliance.com>`_ datafeed for this event is down'''
        url = "status"
        if "if-modified-since" in self.headers:
            del self.headers['if-modified-since']
        response = requests.get(self.base_url + url, headers=self.headers)
        if response.status_code != 200 and response.status_code != 304:
            return True
        data = utils.make_ascii_from_json(response.json())
        return self.event_id in data['down_events'] or data['is_datafeed_down']
