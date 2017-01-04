import requests
import utils
import logging
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

        if behind_threshold is not None:
            self.behind_threshold = behind_threshold

        if not hasattr(self, 'instance'):
            self.basic_url = "http://www.thebluealliance.com/api/v2"
            self.header_key = "X-TBA-App-Id"
            self.header_value = "frc3824:scouting-system:v1"
            if not hasattr(self, 'behind_threshold'):
                self.behind_threshold = 3

            self.instance = True

    def make_request(self, url):
        '''Send request a url

        Args:
            url (`str`): the url where the data is
        '''
        return utils.make_ascii_from_json(requests.get(url, headers={self.header_key: self.header_value}).json())

    def get_event_teams(self):
        '''Gets all the team logistic information for an event'''
        logger.info("Downloading teams from The Blue Alliance for {0:s}".format(self.event_id))
        url = ("{0:s}/event/{1:s}/teams").format(self.basic_url, self.event_id)
        return self.make_request(url)

    def get_event_rankings(self):
        '''Gets all the ranking information for an event'''
        logger.info("Downloading rankings from The Blue Alliance for {0:s}".format(self.event_id))
        url = ("{0:s}/event/{1:s}/rankings").format(self.basic_url, self.event_id)
        return self.make_request(url)

    def get_event_matches(self):
        '''Gets all the match information for an event'''
        logger.info("Downloading matches from The Blue Alliance for {0:s}".format(self.event_id))
        url = ("{0:s}/event/{1:s}/matches").format(self.basic_url, self.event_id)
        return self.make_request(url)

    def is_behind(self, matches):
        '''Checks if `The Blue Alliance <thebluealliance.com>`_ is behind compared to the scouters'''
        completed_matches = len(filter(lambda m: m['comp_level'] == "qm"
                                       and m['score_breakdown'] is not None, self.get_event_matches()))
        return abs(len(matches) - completed_matches) >= self.behind_threshold
