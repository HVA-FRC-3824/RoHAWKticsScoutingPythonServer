from firebase import firebase as fb
from threading import Lock as TLock
from multiprocessing import Lock as PLock
import logging
import os
import json
import time

from ourlogging import setup_logging

from data_models.match import Match
from data_models.team_logistics import TeamLogistics
from data_models.team_calculated_data import TeamCalculatedData
from data_models.team_pit_data import TeamPitData
from data_models.team_ranking_data import TeamRankingData
from data_models.team_pick_ability import TeamPickAbility
from data_models.team_match_data import TeamMatchData
from data_models.super_match_data import SuperMatchData
from data_models.team_qualitative_data import TeamQualitativeData
from data_models.team_pilot_data import TeamPilotData
from data_models.match_pilot_data import MatchPilotData
from data_models.scout_accuracy import ScoutAccuracy

from decorator import attr_check, type_check, singleton, void

setup_logging(__file__)
logger = logging.getLogger(__name__)

#@attr_check
class Database:
    shared_state = {}

    CURRENT = "current"
    PREDICTED = "predicted"
    RANKING_OPTIONS = [CURRENT, PREDICTED]

    FIRST_PICK = "first"
    SECOND_PICK = "second"
    THIRD_PICK = "third"
    PICK_OPTIONS = [FIRST_PICK, SECOND_PICK, THIRD_PICK]

    event_key = str
    base_ref = str
    base_filepath = str
    queued_puts = list
    firebase = fb.FirebaseApplication
    plock = PLock
    tlock = TLock

    @type_check
    def __init__(self, event_key: str=None):
        self.__dict__ = self.shared_state

        if event_key is not None:
            self.event_key = event_key
            self.base_ref = "/{0:s}/".format(self.event_key)
            self.base_filepath = os.path.dirname(os.path.abspath(__file__)) + "/../cached/" + self.event_key + "/"
            self.queued_puts = []
            self.setup_folders()

        if not hasattr(self, 'instance'):
            self.firebase = fb.FirebaseApplication('https://rohawktics-scouting-2017.firebaseio.com/')
            self.plock = PLock()
            self.tlock = TLock()
            self.instance = True

    @type_check
    def setup_folders(self) -> void: 
        for ext in ["schedule", "partial_match", "pit", "super", "pilot/match", "pilot/team",
                    "rankings/predicted", "rankings/current", "logistics", "calculated", "qualitative",
                    "pick/first", "pick/second", "pick/third", "scout_accuracy"]:
            os.makedirs(self.base_filepath + ext, 0o777, True)

    @type_check
    def get_match(self, match_number: int) -> (Match, void):
        '''get information about a match'''
        response = self.get_from_firebase("schedule/", str(match_number))
        if response is None:
            return None
        return Match(response)

    @type_check
    def set_match(self, match: (Match, dict)) -> void:
        '''update the data for a match'''
        if isinstance(match, Match):
            self.set_match(match.to_dict())
        elif isinstance(match, dict):
            self.put_in_firebase("schedule/", str(match['match_number']), match)
        else:
            logger.error("match is not of type Match or dict")

    @type_check
    def set_team_logistics(self, tl: (TeamLogistics, dict)) -> void:
        '''update the logistic information for a team'''
        if isinstance(tl, TeamLogistics):
            self.set_team_logistics(tl.to_dict())
        elif isinstance(tl, dict):
            self.put_in_firebase("logistics/", str(tl['team_number']), tl)
        else:
            logger.error("tl is not of type TeamLogistics or dict")

    @type_check
    def get_team_logistics(self, team_number: int) -> (TeamLogistics, void):
        response = self.get_from_firebase("logistics/", str(team_number))
        if response is None:
            return None
        return TeamLogistics(response)

    @type_check
    def get_team_match_data(self, team_number: int, match_number: int) -> (TeamMatchData, void):
        '''get information about how a team did in a particular match'''
        response = self.get_from_firebase("partial_match/", "{0:d}_{1:d}".format(match_number, team_number))
        if response is None:
            return None
        return TeamMatchData(response)

    def get_all_team_match_data(self) -> dict:
        '''Get a list of how all teams did in each match'''
        response = self.get_from_firebase("partial_match/", "")
        d = {}
        for key, value in response.items():
            if value is not None:
                d[key] = TeamMatchData(value)
        return d

    @type_check
    def set_team_match_data(self, tmd: (TeamMatchData, dict)) -> void:
        if isinstance(tmd, TeamMatchData):
            self.set_team_match_data(tmd.to_dict())
        elif isinstance(tmd, dict):
            self.put_in_firebase("partial_match/", "{0:d}_{1:d}".format(tmd.match_number, tmd.team_number), tmd)
        else:
            logger.error("tmd is not of type TeamMatchData or dict")

    @type_check
    def get_team_pit_data(self, team_number: int) -> (TeamPitData, void):
        response = self.get_from_firebase("pit/", str(team_number))
        if response is None:
            return None
        return TeamPitData(response)

    @type_check
    def set_team_calculated_data(self, tcd: (TeamCalculatedData, dict)) -> void:
        if isinstance(tcd, TeamCalculatedData):
            self.set_team_calculated_data(tcd.to_dict())
        elif isinstance(tcd, dict):
            self.put_in_firebase("calculated/", str(tcd['team_number']), tcd)
        else:
            logger.error("tcd is not of type TeamCalculatedData or dict")

    @type_check
    def get_team_calculated_data(self, team_number: int) -> (TeamCalculatedData, void):
        response = self.get_from_firebase("calculated/", str(team_number))
        if response is None:
            return None
        return TeamCalculatedData(response)

    def get_all_team_calculated_data(self)-> dict:
        '''Get a list of how all teams did in each match'''
        response = self.get_from_firebase("calculated/", "")
        d = {}
        for key, value in response.items():
            if value is not None:
                d[key] = TeamCalculatedData(value)
        return d

    @type_check
    def get_super_match_data(self, match_number: int) -> (SuperMatchData, void):
        response = self.get_from_firebase("super/", str(match_number))
        if response is None:
            return None
        return SuperMatchData(response)

    @type_check
    def get_all_super_match_data(self) -> dict:
        match_number = 1
        super_matches = {}
        nones = 0
        while True:
            smd = self.get_super_match_data(match_number)

            if smd is None:
                nones += 1
            else:
                super_matches[match_number] = smd

            if nones >= 3:
                break

            match_number += 1

        return super_matches

    @type_check
    def set_team_qualitative_data(self, tqd: (TeamQualitativeData, dict)) -> void:
        if isinstance(tqd, TeamQualitativeData):
            self.set_team_qualitative_data(tqd.to_dict)
        elif isinstance(tqd, dict):
            self.put_in_firebase("qualitative/", str(tqd['team_number']), tqd)
        else:
            logger.error("tqd is not of type TeamQualitativeData or dict")

    @type_check
    def get_team_qualitative_data(self, team_number: int) ->(TeamQualitativeData, void):
        response = self.get_from_firebase("qualitative/", str(team_number))
        if response is None:
            return None
        return TeamQualitativeData(response)

    @type_check
    def get_match_pilot_data(self, match_number: int) -> (MatchPilotData, void):
        response = self.get_from_firebase("pilot/match/", str(match_number))
        if response is None:
            return None
        return MatchPilotData(response)

    @type_check
    def set_team_pilot_data(self, tpd: (TeamPilotData, dict)) -> void:
        if isinstance(tpd, TeamPilotData):
            self.set_team_pilot_data(tpd.to_dict())
        elif isinstance(tpd, dict):
            self.put_in_firebase("pilot/team/", str(tpd['team_number']), tpd)
        else:
            logger.error("tqd is not of type TeamPilotData or dict")

    @type_check
    def get_team_ranking_data(self, team_number: int, ranking_type: str) -> (TeamRankingData, void):
        response = self.get_from_firebase("rankings/{0:s}/".format(ranking_type), str(team_number))
        if response is None:
            return None
        return TeamRankingData(response)

    @type_check
    def set_team_ranking_data(self, trd: (TeamRankingData, dict), ranking_type: str) -> void:
        if isinstance(trd, TeamRankingData):
            self.set_team_ranking_data(trd.to_dict(), ranking_type)
        elif isinstance(trd, dict):
            self.put_in_firebase("rankings/{0:s}/".format(ranking_type), trd['team_number'], trd)
        else:
            logger.error("trd is not of type TeamRankingData or dict")

    @type_check
    def get_team_pick_ability(self, team_number: int, pick_type: str) -> (TeamPickAbility, void):
        response = self.get_from_firebase("pick/{0:s}/".format(pick_type), str(team_number))
        if response is None:
            return None
        return TeamPickAbility(response)

    @type_check
    def set_team_pick_ability(self, tpa: (TeamPickAbility, dict), pick_type: str) -> void:
        if isinstance(tpa, TeamPickAbility):
            self.set_team_pick_ability(tpa.to_dict(), pick_type)
        elif isinstance(tpa, dict):
            self.put_in_firebase("pick/{0:s}/".format(pick_type), tpa['team_number'], tpa)
        else:
            logger.error("tpa is not of type TeamPickAbility or dict")

    @type_check
    def get_scout_accuracy(self, scout_name: str) -> (ScoutAccuracy, void):
        response = self.get_from_firebase("scout_accuracy/", scout_name)
        if response is not None:
            return None
        return ScoutAccuracy(response)

    @type_check
    def set_scout_accuracy(self, sa: (ScoutAccuracy, dict)) -> void:
        if isinstance(sa, ScoutAccuracy):
            self.set_scout_accuracy(sa.to_dict())
        elif isinstance(sa, dict):
            self.put_in_firebase("scout_accuracy/", sa['name'], sa)
        else:
            logger.error("sa is not of type ScoutAccuracy or dict")

    @type_check
    def get_from_firebase(self, location: str, key: str) -> (dict, void):
        '''Grabs the specified location from firebase. If data has not been updated then local
        cache is used.'''
        if location[-1] != '/':
            location += '/'

        logger.debug('GET - Location: {} Key: {}'.format(location, key))

        # Get cached version if exists
        if os.path.isfile(self.base_filepath + location + key + '.json'):
            with open(self.base_filepath + location + key + '.json') as f:
                cached_data = json.loads(f.read())
            # 3 attempts to get last_modified variable
            for i in range(3):
                try:
                    response = self.firebase.get(self.base_ref + location + key, 'last_modified')
                    # Catch exception and try again
                except:
                    logger.warning('Caught error with getting timestamp')
                    # if successful (no exception)
                else:
                    # if data needs to be pulled
                    if response is None or response > cached_data['last_modified']:
                        del response
                        # 3 attempts
                        for j in range(3):
                            try:
                                response = self.firebase.get(self.base_ref + location, key)
                            # Catch exception and try again
                            except:
                                logger.warning('Caught error with getting data from firebase. Attempt {}'.format(j + 1))
                            # Successfully pulled response
                            else:
                                # Nothing is in that location
                                if response is None:
                                    return None
                                # Record cached version
                                with open(self.base_filepath + location + key + '.json', 'w') as f:
                                    f.write(json.dumps(response, sort_keys=True, indent=4))
                                return response
                        # 3 failures probably means that there is an issue with the internet connection
                        # return the cached version until it is fixed
                        return cached_data
                    # no new information, so return the cached version
                    else:
                        return cached_data
        # No cached version
        else:
            # 3 attempts
            for i in range(3):
                try:
                    response = self.firebase.get(self.base_ref + location, key)
                # Catch exception and try again
                except:
                    logger.warning('Caught exception with getting data from firebase. Attempt {}'.format(i))
                # Successfully pulled a response
                else:
                    # Nothing in that location in firebase
                    if response is None:
                        return None

                    # Record cached version
                    with open(self.base_filepath + location + key + ".json", 'w') as f:
                        f.write(json.dumps(response, sort_keys=True, indent=4))
                    return response
            # 3 failures probably means there is an issue with the internet connection
            # There is no cached version, so return None
            return None

    @type_check
    def put_in_firebase(self, location: str, key: str, d: dict, empty_queue: bool=True) -> void:
        '''Updates firebase at the specified location and write to file'''
        self.tlock.acquire()
        self.plock.acquire()

        if(location[-1] != '/'):
            location += '/'

        logger.debug("PUT - Location: {} Key: {}".format(location, key))

        # last_modified is a long in milliseconds (due to android)
        d['last_modified'] = int(time.time() * 1000)
        key = str(key)
        # 3 attempts
        for i in range(3):
            try:
                self.firebase.put(url=self.base_ref + location, name=key, data=d)
            # Catch exception and try again
            except:
                logger.warning("Caught error with putting data in firebase. Attempt {}".format(i + 1))
            else:
                self.tlock.release()
                self.plock.release()
                with open(self.base_filepath + location + key + ".json", "w") as f:
                    f.write(json.dumps(d, sort_keys=True, indent=4))
                # empty the queue of failed puts
                if empty_queue:
                    puts = self.queued_puts
                    self.queued_puts = []
                    for put in puts:
                        self.put_in_firebase(put[0], put[1], put[2], False)
                return
        self.tlock.release()
        self.plock.release()
        # 3 failures probably means there is an issue with the internet connection
        self.queued_puts.append((location, key, d))
