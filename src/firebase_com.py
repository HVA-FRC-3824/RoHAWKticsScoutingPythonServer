import json
import datetime
from firebase import firebase as fb
import os
import time
# import traceback

from threading import Lock as TLock
from multiprocessing import Lock as PLock

from constants import Constants

from data_models.match import Match
from data_models.team import Team
from data_models.team_logistics import TeamLogistics
from data_models.team_pit_data import TeamPitData
from data_models.team_match_data import TeamMatchData
from data_models.super_match_data import SuperMatchData
from data_models.team_dt_feedback import TeamDTFeedback
from data_models.team_pick_ability import TeamPickAbility
from data_models.team_ranking_data import TeamRankingData
from data_models.team_calculated_data import TeamCalculatedData
from data_models.scout_accuracy import ScoutAccuracy
from data_models.strategy import Strategy
from data_models.strategy_suggestion import StrategySuggestion

import logging
from ourlogging import setup_logging
setup_logging(__file__)
logger = logging.getLogger(__name__)


(secret, url) = ('TSkriBv7Z81MpfvsUM332f4HmtoAOjSUiN5xRLAb',
                 'https://rohawktics-scouting-2017.firebaseio.com/')


class FirebaseCom:
    '''Singleton class for communicating with firebase'''
    EVENT_ID = ""
    shared_state = {}

    def __init__(self, event_id=None):
        self.__dict__ = self.shared_state
        if event_id is not None and event_id != self.EVENT_ID:
            self.matches = []
            self.teams = []
            self.event_id = self.EVENT_ID = event_id
            self.base_ref = "/{0:s}/".format(self.event_id)
            self.base_filepath = os.path.dirname(os.path.abspath(__file__)) + "/../cached/" + self.event_id + "/"
            self.setup_folders()

        if not hasattr(self, "instance"):
            self.instance = True
            self.plock = PLock()
            self.tlock = TLock()
            self.firebase = fb.FirebaseApplication(url)
            self.queued_puts = []

    def setup_folders(self):
        for ext in ["schedule", "partial_match", "pit", "super_match", "feedback",
                    "rankings/predicted", "rankings/current", "info", "calculated",
                    "first_pick", "second_pick", "third_pick", "scout_accuracy", "strategy"]:
            os.makedirs(self.base_filepath + ext, 0o777, True)

    def update_match(self, match):
        '''update logistics information about a match (who was in it, score breakdown, etc)'''
        if isinstance(match, Match):
            self.update_match(match.to_dict())
        elif isinstance(match, dict):
            self.put_in_firebase("schedule/", "{0:d}".format(match['match_number']), match)
        else:
            logger.error("match variable not a Match object or dict")
            raise TypeError("match variable not a Match object or dict")

    def get_match(self, match_number):
        '''get logistics information about a match (who was in it, score breakdown, etc)'''
        response = self.get_from_firebase("schedule/", str(match_number))
        if response is None:
            return None
        return Match(response)

    def get_all_matches(self):
        '''get logistics information for all matches'''
        d = {}
        for match_number in range(1, Constants().number_of_matches):
            response = self.get_match(match_number)
            if response is not None:
                d[match_number] = response
        return d

    def update_team_match_data(self, tmd):
        '''update the match data for a specific team that was in that match'''
        if isinstance(tmd, TeamMatchData):
            self.update_team_match_data(tmd.to_dict())
        elif isinstance(tmd, dict):
            self.put_in_firebase("partial_match/",
                                 "{0:d}_{1:d}".format(tmd['match_number'],
                                                      tmd['team_number']), tmd)
            response = self.get_from_firebase("partial_match/", "scout_names")
            if response is None:
                list_ = []
                list_.append(tmd['scout_name'])
                self.put_in_firebase("partial_match/", "scout_names", {'list': list_})
            elif tmd['scout_name'] not in response['list']:
                response['list'].append(tmd['scout_name'])
                self.put_in_firebase("partial_match/", "scout_names", response)
        else:
            logger.error("tmd variable not a TeamMatchData object or dict")
            raise TypeError("tmd variable not a TeamMatchData object or dict")

    def get_team_match_data(self, team_number, match_number):
        '''get the match data for a specific team in a specific match'''
        response = self.get_from_firebase("partial_match/", "{0:d}_{1:d}".format(int(match_number),
                                                                                 int(team_number)))
        if response is None:
            return None
        return TeamMatchData(response)

    def get_all_team_match_data(self):
        '''get the match data for each team for each match'''
        d = {}
        for match_number in range(1, Constants().number_of_matches):
            match = self.get_match(match_number)
            if match is None:
                continue
            for team_number in match.teams:
                response = self.get_team_match_data(match_number=match_number, team_number=team_number)
                if response is not None:
                    d["{0:d}_{1:d}".format(match_number, team_number)] = response
        return d

    def update_team_pit_data(self, tpd):
        '''update the pit data for a specific team'''
        if isinstance(tpd, TeamPitData):
            self.update_team_pit_data(tpd.to_dict())
        elif isinstance(tpd, dict):
            self.put_in_firebase("pit/", str(tpd['team_number']), tpd)
        else:
            logger.error("tpd variable not a TeamPitData object or dict")
            raise TypeError("tpd variable not a TeamPitData object or dict")

    def get_team_pit_data(self, team_number):
        '''get the pit data for a specific team'''
        response = self.get_from_firebase("pit/", str(team_number))
        if response is None:
            return None
        return TeamPitData(response)

    def get_all_team_pit_data(self):
        '''get the pit data for all teams'''
        d = {}
        for team_number in Constants().team_numbers:
            response = self.get_team_pit_data(team_number)
            if response is not None:
                d[team_number] = response
        return response

    def update_super_match_data(self, smd):
        '''update the super scout data for a specific match'''
        if isinstance(smd, SuperMatchData):
            self.update_super_match_data(smd.to_dict())
        elif isinstance(smd, dict):
            self.put_in_firebase("super_match/", str(smd['match_number']), smd)
        else:
            logger.error("smd variable is not a SuperMatchData object or dict")
            raise TypeError("smd variable is not a SuperMatchData object or dict")

    def get_super_match_data(self, match_number):
        '''get the super scout data for a specific match'''
        response = self.get_from_firebase("super_match/", str(match_number))
        if response is None:
            return None
        return SuperMatchData(response)

    def get_all_super_match_data(self):
        '''get the super scout data for all matches'''
        d = {}
        for match_number in range(1, Constants().number_of_matches):
            response = self.get_super_match_data(match_number)
            if response is not None:
                d[match_number] = response
        return d

    def update_team_dt_feedback(self, tdtf):
        '''update the drive team's feedback about a specific team'''
        if isinstance(tdtf, TeamDTFeedback):
            self.update_team_dt_feedback(tdtf.to_dict)
        elif isinstance(tdtf, dict):
            self.put_in_firebase("feedback/", str(tdtf['team_number']), tdtf)
        else:
            logger.error("tdtf variable is not a TeamDTFeedback object or dict")
            raise TypeError("tdtf variable is not a TeamDTFeedback object or dict")

    def get_team_dt_feedback(self, team_number):
        '''get the drive team's feedback about a specific team'''
        response = self.get_from_firebase("feedback/", str(team_number))
        if response is None:
            return None
        return TeamDTFeedback(response)

    def get_all_team_dt_feedback(self):
        '''get all the drive team's feedback'''
        our_number = Constants().OUR_TEAM_NUMBER
        us = self.get_from_firebase("info/", str(our_number))
        d = {}
        for match_number in us.matches:
            match = self.get_match(match_number)
            if match.is_blue(our_number):
                for i in range(3):
                    if i == our_number:
                        continue
                    response = self.get_team_dt_feedback(match.teams[i])
                    if response is not None:
                        d[match.teams[i]] = response
            else:
                for i in range(3, 3):
                    if i == our_number:
                        continue
                    response = self.get_team_dt_feedback(match.teams[i])
                    if response is not None:
                        d[match.teams[i]] = response
        return d

    def update_team_logistics(self, tl):
        '''update the logistics information about a specific team (nickname, match numbers, etc)'''
        if isinstance(tl, TeamLogistics):
            self.update_team_logistics(tl.to_dict())
        elif isinstance(tl, dict):
            self.put_in_firebase("info/", tl['team_number'], tl)
        else:
            logger.error("tl variable is not a TeamLogistics object or dict")
            raise TypeError("tl variable is not a TeamLogistics object or dict")

    def get_team_logistics(self, team_number):
        '''get the logistics information about a specific team (nickname, match numbers, etc)'''
        response = self.get_from_firebase("info/", str(team_number))
        if response is None:
            return None
        return TeamLogistics(response)

    def get_all_team_logistics(self):
        '''get the logistics information for all teams'''
        d = {}
        for team_number in Constants().team_numbers:
            response = self.get_team_logistics(team_number)
            if response is not None:
                d[team_number] = response
        return d

    def update_team_calculated_data(self, tcd):
        '''update the calculated data for a specific team'''
        if isinstance(tcd, TeamCalculatedData):
            self.update_team_calculated_data(tcd.to_dict())
        elif isinstance(tcd, dict):
            self.put_in_firebase("calculated", str(tcd['team_number']), tcd)
        else:
            logger.error("tcd variable is not a TeamCalculatedData object or dict")
            raise TypeError("tcd variable is not a TeamCalculatedData object or dict")

    def get_team_calculated_data(self, team_number):
        '''get the calculated data for a specific team'''
        response = self.get_from_firebase("calculated/", str(team_number))
        if response is None:
            return None
        return TeamCalculatedData(response)

    def get_all_team_calculated_data(self):
        '''get the calculated data for all teams'''
        d = {}
        for team_number in Constants().team_numbers:
            response = self.get_team_calculated_data(team_number)
            if response is not None:
                d[team_number] = response
        return d

    def update_current_team_ranking_data(self, trd):
        '''update the current ranking data on a specific team'''
        if isinstance(trd, TeamRankingData):
            self.update_current_team_ranking_data(trd.to_dict())
        elif isinstance(trd, dict):
            self.put_in_firebase("rankings/current/", str(trd['team_number']), trd)
        else:
            logger.error("c trd variable is not a TeamRankingData object or dict")
            raise TypeError("c trd variable is not a TeamRankingData object or dict")

    def get_current_team_ranking_data(self, team_number):
        '''get the current ranking data on a specific team'''
        response = self.get_from_firebase("rankings/current/", str(team_number))
        if response is None:
            return None
        return TeamRankingData(response)

    def get_all_current_team_ranking_data(self):
        '''get the current rankings for all of the teams at the event'''
        d = {}
        for team_number in Constants().team_numbers:
            response = self.get_current_team_ranking_data(team_number)
            if response is not None:
                d[team_number] = response
        return d

    def update_predicted_team_ranking_data(self, trd):
        '''update the predicted ranking data on a specific team'''
        if isinstance(trd, TeamRankingData):
            self.update_predicted_team_ranking_data(trd.to_dict())
        elif isinstance(trd, dict):
            self.put_in_firebase("rankings/predicted/", str(trd['team_number']), trd)
        else:
            logger.error("p trd variable is not a TeamRankingData object or dict")
            raise TypeError("p trd variable is not a TeamRankingData object or dict")

    def get_predicted_team_ranking_data(self, team_number):
        '''get the predicted ranking data on a specific team'''
        response = self.get_from_firebase("rankings/predicted/", str(team_number))
        if response is None:
            return None
        return TeamRankingData(response)

    def get_all_predicted_team_ranking_data(self):
        '''get the predicted ranking data for all teams'''
        d = {}
        for team_number in Constants().team_numbers:
            response = self.get_predicted_team_ranking_data(team_number)
            if response is not None:
                d[team_number] = response
        return d

    def update_team_first_pick_ability(self, tpa):
        '''update the first pick ability data for a specific team'''
        if isinstance(tpa, TeamPickAbility):
            self.update_team_first_pick_ability(tpa.to_dict())
        elif isinstance(tpa, dict):
            self.put_in_firebase("first_pick", str(tpa['team_number']), tpa)
        else:
            logger.error("1st tpa variable is not a TeamPickAbility object or dict")
            raise TypeError("1st tpa variable is not a TeamPickAbility object or dict")

    def get_team_first_pick_ability(self, team_number):
        '''get the first pick ability data for a specific team'''
        response = self.get_from_firebase("first_pick/", str(team_number))
        if response is None:
            return None
        return TeamPickAbility(response)

    def get_all_team_first_pick_ability(self):
        '''get the first pick ability for all teams'''
        d = {}
        for team_number in Constants().team_numbers:
            response = self.get_team_first_pick_ability(team_number)
            if response is not None:
                d[team_number] = response
        return d

    def update_team_second_pick_ability(self, tpa):
        '''update the second pick ability data for a specific team'''
        if isinstance(tpa, TeamPickAbility):
            self.update_team_second_pick_ability(tpa.to_dict())
        elif isinstance(tpa, dict):
            self.put_in_firebase("second_pick", str(tpa['team_number']), tpa)
        else:
            logger.error("2nd tpa variable is not a TeamPickAbility object or dict")
            raise TypeError("2nd tpa variabel is not a TeamPickAbility object or dict")

    def get_team_second_pick_ability(self, team_number):
        '''get the second pick ability data for a specific team'''
        response = self.get_from_firebase("second_pick/", str(team_number))
        if response is None:
            return None
        return TeamPickAbility(response)

    def get_all_team_second_pick_ability(self):
        '''get the second pick ability data for all teams'''
        d = {}
        for team_number in Constants().team_numbers:
            response = self.get_team_second_pick_ability(team_number)
            if response is not None:
                d[team_number] = response
        return d

    def update_team_third_pick_ability(self, tpa):
        '''update the third pick ability data for a specific team'''
        if isinstance(tpa, TeamPickAbility):
            self.update_team_third_pick_ability(tpa.to_dict())
        elif isinstance(tpa, dict):
            self.put_in_firebase("third_pick", str(tpa['team_number']), tpa)
        else:
            logger.error("3rd tpa variable is not a TeamPickAbility object or dict")
            raise TypeError("3rd tpa variable is not a TeamPickAbility object or dict")

    def get_team_third_pick_ability(self, team_number):
        '''get the third pick ability data for a specific team'''
        response = self.get_from_firebase("third_pick/", str(team_number))
        if response is None:
            return None
        return TeamPickAbility(response)

    def get_all_team_third_pick_ability(self):
        '''get the third pick data for all teams'''
        d = {}
        for team_number in Constants().team_numbers:
            response = self.get_team_third_pick_ability(team_number)
            if response is not None:
                d[team_number] = response
        return d

    def update_team(self, team):
        '''update all the data for a specific team'''
        if isinstance(team, Team):
            self.update_team(team.to_dict())
        elif isinstance(team, dict):
            self.update_team_logistics(team['info'])
            self.update_team_pit_data(team['pit'])
            self.update_team_dt_feedback(team['drive_team_feedback'])
            self.update_team_calculated_data(team['calc'])
            self.update_current_team_ranking_data(team['current_ranking'])
            self.update_predicted_team_ranking_data(['predicted_ranking'])
            self.update_team_first_pick_ability(team['first_pick'])
            self.update_team_second_pick_ability(team['second_pick'])
            self.update_team_third_pick_ability(team['third_pick'])
            for tmd in team['completed_matches'].values():
                self.update_team_match_data(tmd)
        else:
            logger.error("team variable is not Team object or dict")
            raise TypeError("team variable is not Team object or dict")

    def get_team(self, team_number):
        '''get all the data for a specific team'''
        team = Team()
        team.team_number = team_number
        team.info = self.get_team_logistics(team_number)
        team.pit = self.get_team_pit_data(team_number)
        team.drive_team_feedback = self.get_team_dt_feedback(team_number)
        team.calc = self.get_team_calculated_data(team_number)
        team.current_ranking = self.get_current_team_ranking_data(team_number)
        team.predicted_ranking = self.get_predicted_team_ranking_data(team_number)
        team.first_pick = self.get_team_first_pick_ability(team_number)
        team.second_pick = self.get_team_second_pick_ability(team_number)
        team.third_pick = self.get_team_third_pick_ability(team_number)
        for match_number in team.info.match_numbers:
            tmd = self.get_team_match_data(team_number=team_number, match_number=match_number)
            if tmd is not None:
                team.completed_matches[match_number] = tmd
            else:
                break
        return team

    def get_teams(self):
        '''get a list of all the teams'''
        return {x: self.get_team(x) for x in Constants().team_numbers}

    def update_scout_accuracy(self, scout):
        '''update the data for scout accuracy'''
        if isinstance(scout, ScoutAccuracy):
            self.update_scout_accuracy(scout.to_dict())
        elif isinstance(scout, dict):
            self.put_in_firebase("scout_accuracy/", scout['name'].replace(" ", "_"), scout)
        else:
            logger.error("scout_analysis variable is not a ScoutAccuracy or dict")
            raise Exception("scout_analysis variable is not a ScoutAccuracy or dict")

    def get_scout_accuracy(self, scout_name):
        '''get the data for scout accuracy'''
        response = self.get_from_firebase("scout_accuracy/", scout_name.replace(" ", "_"))
        if response is None:
            return None
        return ScoutAccuracy(response)

    def get_all_scout_accuracy(self):
        '''get all the data for scout accuracy'''
        d = {}
        for scout_name in self.get_from_firebase("partial_match/", "scout_names")['list']:
            response = self.get_scout_accuracy(scout_name)
            if response is not None:
                d[scout_name] = response
        return d

    def update_strategy(self, strategy):
        '''update the data for the strategy'''
        if isinstance(strategy, Strategy):
            self.update_strategy(strategy.to_dict())
        elif isinstance(strategy, dict):
            self.put_in_firebase("strategy/drawings", strategy['name'], strategy)

            # Append to the list of strategy names to be used in get all strategies
            response = self.get_from_firebase("strategy/", "drawing_names")
            if response is None:
                list_ = []
                list_.append(strategy['name'])
                self.put_in_firebase("strategy/", "drawing_names", {'list': list_})
            elif strategy['name'] not in response['list']:
                response['list'].append(strategy['name'])
                self.put_in_firebase("strategy/", "drawing_names", response)
        else:
            logger.error("strategy variable is not a Strategy or dict")
            raise Exception("strategy variable is not a Strategy or dict")

    def get_strategy(self, strategy_name):
        '''get all data for a strategy'''
        response = self.get_from_firebase("strategy/drawings/", strategy_name)
        if response is None:
            return None
        return Strategy(response)

    def get_all_strategies(self):
        '''get all individual strategies'''
        d = {}
        for strategy_name in self.get_from_firebase("strategy/", "drawing_names")['list']:
            response = self.get_strategy(strategy_name)
            if response is not None:
                d[strategy_name] = response
        return d

    def update_strategy_suggestion(self, strategy_suggestion):
        '''update the data for scout accuracy'''
        if isinstance(strategy_suggestion, StrategySuggestion):
            self.update_strategy_suggestion(strategy_suggestion.to_dict())
        elif isinstance(strategy_suggestion, dict):
            self.put_in_firebase("strategy/suggestions/", strategy_suggestion['key'], strategy_suggestion)

            # Append to the list of strategy suggestions keys to be used in get all strategy suggestions
            response = self.get_from_firebase("strategy/", "suggestion_keys")
            if response is None:
                list_ = []
                list_.append(strategy_suggestion['key'])
                self.put_in_firebase("strategy/", "suggestion_keys", {'list': list_})
            elif strategy_suggestion['key'] not in response['list']:
                response['list'].append(strategy_suggestion['key'])
                self.put_in_firebase("strategy/", "suggestion_keys", response)
        else:
            logger.error("strategy_suggestion variable is not a StrategySuggestion or dict")
            raise Exception("strategy_suggestion variable is not a StrategySuggestion or dict")

    def get_strategy_suggestion(self, strategy_suggestion_key):
        '''get all data for a strategy suggestion'''
        response = self.get_from_firebase("strategy/suggestions/", strategy_suggestion_key)
        if response is None:
            return None
        return StrategySuggestion(response)

    def get_all_strategy_suggestions(self):
        '''get all individual strategy suggestions'''
        d = {}
        for strategy_suggestion_key in self.get_from_firebase("strategy/", "suggestion_keys")['list']:
            response = self.get_strategy_suggestion(strategy_suggestion_key)
            if response is not None:
                d[strategy_suggestion_key] = response
        return d

    def get_from_firebase(self, location, key):
        '''Grabs the specified location from firebase if new data if not then
           grabs from file
        '''

        if(location[-1] != '/'):
            location += '/'

        logger.info("GET - Location: {} Key: {}".format(location, key))

        # Get cached version if exists
        if os.path.isfile(self.base_filepath + location + key + ".json"):
            with open(self.base_filepath + location + key + ".json") as f:
                json_dict = json.loads(f.read())
            # 3 attempts to get last_modified variable
            for i in range(3):
                try:
                    response = self.firebase.get(self.base_ref + location + key, "last_modified")
                # Catch exception and try again
                except:
                    logger.warning("Caught error with getting timestamp")
                # if successful (no exception)
                else:
                    # if data needs to be pulled
                    if response is None or response > json_dict['last_modified']:
                        del response
                        # 3 attempts
                        for j in range(3):
                            try:
                                response = self.firebase.get(self.base_ref + location, key)
                            # Catch exception and try again
                            except:
                                logger.warning("Caught error with getting data from firebase. Attempt {}".format(j + 1))
                            else:
                                # Successfully pulled a response

                                # Nothing in that location in the database
                                if response is None:
                                    return None
                                # Record cached version
                                with open(self.base_filepath + location + key + ".json", 'w') as f:
                                    f.write(json.dumps(response, sort_keys=True, indent=4))
                                return response
                        # 3 failures probably means there is an issue with the internet connection
                        # return the cached version until internet connection is fixed
                        return json_dict

                    # if no new information return cached version
                    else:
                        return json_dict
            # 3 failures probably means there is an issue with the internet connection
            # return the cached version until internet connection is fixed
            return json_dict
        # No cached version
        else:
            # 3 attempts
            for i in range(3):
                try:
                    response = self.firebase.get(self.base_ref + location, key)
                # Catch exception and try again
                except:
                    logger.warning("Caught error with getting data from firebase. Attempt {}".format(i + 1))
                else:
                    # Successfully pulled a response

                    # Nothing in that location in the database
                    if response is None:
                        return None
                    # Record cached version
                    with open(self.base_filepath + location + key + ".json", "w") as f:
                        f.write(json.dumps(response, sort_keys=True, indent=4))
                    return response
            # 3 failures probably means there is an issue with the internet connection
            # No cached version to return
            return None

    def put_in_firebase(self, location, key, d, empty_queue=True):
        '''Updates firebase at the specified location and write to file'''
        self.tlock.acquire()
        self.plock.acquire()

        if(location[-1] != '/'):
            location += '/'

        logger.info("PUT - Location: {} Key: {}".format(location, key))

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

    def cache(self):
        '''Cache the firebase to a json file'''
        while True:
            try:
                data = json.dumps(self.firebase.get("/", None), indent=4)
                now = str(datetime.datetime.now())
                with open("{0:s}/cached/{1:s}.json".format(self.base_filepath, now), 'w') as f:
                    f.write(data)
                    f.close()
                    break
            except:
                logger.error("Error with caching firebase")
