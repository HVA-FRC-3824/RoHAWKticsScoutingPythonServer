import requests
import json
import utils


class TheBlueAlliance:
    def __init__(self, event_id):
        self.event_id = event_id
        self.basic_url = "http://www.thebluealliance.com/api/v2"
        self.header_key = "X-TBA-App-Id"
        self.header_value = "frc3824:scouting-system:v1"

    def make_request(self, url):
        return utils.make_ascii_from_json(requests.get(url, headers={self.header_key: self.header_value}).json())

    def get_event_teams(self):
        url = ("{0:s}/event/{1:s}/teams").format(self.basic_url, self.event_id)
        return self.make_request(url)

    def get_event_rankings(self):
        url = ("{0:s}/event/{1:s}/rankings").format(self.basic_url, self.event_id)
        return self.make_request(url)

    def get_event_matches(self):
        url = ("{0:s}/event/{1:s}/matches").format(self.basic_url, self.event_id)
        return self.make_request(url)

    def is_behind(self, matches):
        completed_matches = len(filter(lambda m: m['comp_level'] == "qm"
                                       and m['score_breakdown'] is not None, self.get_event_matches()))
        return abs(len(matches) - completed_matches) >= 3
