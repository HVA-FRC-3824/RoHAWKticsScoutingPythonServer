import json
import datetime
from firebase import firebase as fb
import utils

from threading import Lock as TLock
from multiprocessing import Lock as PLock

from DataModels.match import Match
from DataModels.team import Team
from DataModels.team_logistics import TeamLogistics
from DataModels.team_pit_data import TeamPitData
from DataModels.team_match_data import TeamMatchData
from DataModels.super_match_data import SuperMatchData
from DataModels.team_dt_feedback import TeamDTFeedback
from DataModels.team_pick_ability import TeamPickAbility
from DataModels.team_ranking_data import TeamRankingData
from DataModels.team_calculated_data import TeamCalculatedData

import logging
from ourlogging import setup_logging
setup_logging(__file__)
logger = logging.getLogger(__name__)


# TODO: add authentication

(secret, url) = ('TSkriBv7Z81MpfvsUM332f4HmtoAOjSUiN5xRLAb',
                 'https://rohawktics-scouting-2017.firebaseio.com/')

# auth = fb.FirebaseAuthentication(secret, "", True, True)

firebase = fb.FirebaseApplication(url)


class FirebaseCom:
    EVENT_ID = ""
    shared_state = {}

    def __init__(self, event_id=None):
        self.__dict__ = self.shared_state
        if event_id is not None and event_id != self.EVENT_ID:
            self.matches = []
            self.teams = []
            self.event_id = self.EVENT_ID = event_id
            self.base_ref = "/{0:s}".format(self.event_id)
        if not hasattr(self, "instance"):
            self.instance = True
            self.plock = PLock()
            self.tlock = TLock()

    def update_match(self, match):
        # update logistics information about a match (who was in it, score breakdown, etc)
        ref = "{0:s}/schedule".format(self.base_ref)
        if isinstance(match, Match):
            self.update_match(match.to_dict())
        elif isinstance(match, dict):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(match['match_number']), match)
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating match {0:d}".format(match['match_number']))
                raise Exception("Error updateing match {0:d}".format(match['match_number']))
        else:
            logger.e("match variable not a Match object or dict")
            raise TypeError("match variable not a Match object or dict")

    def get_match(self, match_number):
        # get logistics information about a match (who was in it, score breakdown, etc)
        ref = "{0:s}/schedule/{1:d}".format(self.base_ref, match_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return Match(match_number=match_number)
        return Match(**response)

    def update_team_match_data(self, tmd):
        # update the match data for a specific team that was in that match
        ref = "{0:s}/partial_match".format(self.base_ref)
        if isinstance(tmd, TeamMatchData):
            self.update_team_match_data(tmd.to_dict())
        elif isinstance(tmd, dict):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}_{1:d}".format(tmd['match_number'], tmd['team_number']), tmd)
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.error("Error updating tmd with match number{0:d} and team number {1:d}"
                             .format(tmd['match_number'], tmd['team_number']))
                raise Exception("Error updating tmd with match {0:d} and team number {1:d}"
                                .format(tmd['match_number'], tmd['team_number']))
        else:
            logger.error("tmd variable not a TeamMatchData object or dict")
            raise TypeError("tmd variable not a TeamMatchData object or dict")

    def get_team_match_data(self, team_number, match_number):
        # get the match data for a specific team in a specific match
        ref = "{0:s}/partial_match/{1:d}_{2:d}".format(self.base_ref, match_number, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return TeamMatchData(team_number=team_number, match_number=match_number)
        return TeamMatchData(**response)

    def get_all_team_match_data(self):
        ref = "{0:s}/partial_match".format(self.base_ref)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return {}
        for key, tmd in iter(response.items()):
            response[key] = TeamMatchData(**tmd)
        return response

    def update_team_pit_data(self, tpd):
        # update the pit data for a specific team
        ref = "{0:s}/pit".format(self.base_ref)
        if isinstance(tpd, TeamPitData):
            self.update_team_pit_data(tpd.to_dict())
        elif isinstance(tpd, dict):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(tpd['team_number']), tpd)
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating tpd {0:d}".format(tpd['team_number']))
                raise Exception("Error updating tpd {0:d}".format(tpd['team_number']))
        else:
            logger.e("tpd variable not a TeamPitData object or dict")
            raise TypeError("tpd variable not a TeamPitData object or dict")

    def get_team_pit_data(self, team_number):
        # get the pit data for a specific team
        ref = "{0:s}/pit/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return TeamPitData(team_number=team_number)
        return TeamPitData(**response)

    def update_super_match_data(self, smd):
        # update the super scout data for a specific match
        ref = "{0:s}/super_match".format(self.base_ref)
        if isinstance(smd, SuperMatchData):
            self.update_super_match_data(smd.to_dict())
        elif isinstance(smd, dict):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(smd['match_number']), smd)
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating smd {0:d}".format(smd['match_number']))
                raise Exception("Error updating smd {0:d}".format(smd['match_number']))
        else:
            logger.e("smd variable is not a SuperMatchData object or dict")
            raise TypeError("smd variable is not a SuperMatchData object or dict")

    def get_super_match_data(self, match_number):
        # get the super scout data for a specific match
        ref = "{0:s}/super_match/{1:d}".format(self.base_ref, match_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return SuperMatchData(match_number=match_number)
        return SuperMatchData(**response)

    def get_all_super_match_data(self):
        ref = "{0:s}/super_match".format(self.base_ref)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return []
        for key, value in iter(response.items()):
            response[key] = SuperMatchData(**value)
        return response

    def update_team_dt_feedback(self, tdtf):
        # update the drive team's feedback about a specific team
        ref = "{0:s}/feedback".format(self.base_ref)
        if isinstance(tdtf, TeamDTFeedback):
            self.update_team_dt_feedback(tdtf.to_dict)
        elif isinstance(tdtf, dict):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(tdtf['team_number']), tdtf)
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating tdtf {0:d}".format(tdtf['team_number']))
                raise Exception("Error updating tdtf {0:d}".format(tdtf['team_number']))
        else:
            logger.e("tdtf variable is not a TeamDTFeedback object or dict")
            raise TypeError("tdtf variable is not a TeamDTFeedback object or dict")

    def get_team_dt_feedback(self, team_number):
        # get the drive team's feedback about a specific team
        ref = "{0:s}/feedback/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return TeamDTFeedback(team_number=team_number)
        return TeamDTFeedback(**response)

    def update_team_logistics(self, tl):
        # update the logistics information about a specific team (nickname, match numbers, etc)
        ref = "{0:s}/info".format(self.base_ref)
        if isinstance(tl, TeamLogistics):
            self.update_team_logistics(tl.to_dict())
        elif isinstance(tl, dict):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(tl['team_number']), tl)
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating tl {0:d}".format(tl['team_number']))
                raise Exception("Error updating tl {0:d}".format(tl['team_number']))
        else:
            logger.e("tl variable is not a TeamLogistics object or dict")
            raise TypeError("tl variable is not a TeamLogistics object or dict")

    def get_team_logistics(self, team_number):
        # get the logistics information about a specific team (nickname, match numbers, etc)
        ref = "{0:s}/info/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return TeamLogistics(team_number=team_number)
        return TeamLogistics(**response)

    def update_team_calculated_data(self, tcd):
        # update the calculated data for a specific team
        ref = "{0:s}/calculated".format(self.base_ref)
        if isinstance(tcd, TeamCalculatedData):
            self.update_team_calculated_data(tcd.to_dict())
        elif isinstance(tcd, dict):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(tcd['team_number']), tcd)
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.error("Error updating tcd {0:d}".format(tcd['team_number']))
                raise Exception("Error updating tcd {0:d}".format(tcd['team_number']))
        else:
            logger.error("tcd variable is not a TeamCalculatedData object or dict")
            raise TypeError("tcd variable is not a TeamCalculatedData object or dict")

    def get_team_calculated_data(self, team_number):
        # get the calculated data for a specific team
        ref = "{0:s}/calculated/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return TeamCalculatedData(team_number=team_number)
        return TeamCalculatedData(**response)

    def update_current_team_ranking_data(self, trd):
        # update the current ranking data on a specific team
        ref = "{0:s}/rankings/current".format(self.base_ref)
        if isinstance(trd, TeamRankingData):
            self.update_current_team_ranking_data(trd.to_dict())
        elif isinstance(trd, dict):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(trd['team_number']), trd)
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating c trd {0:d}".format(trd['team_number']))
                raise Exception("Error updating c trd {0:d}".format(trd['team_number']))
        else:
            logger.e("c trd variable is not a TeamRankingData object or dict")
            raise TypeError("c trd variable is not a TeamRankingData object or dict")

    def get_current_team_ranking_data(self, team_number):
        # get the current ranking data on a specific team
        ref = "{0:s}/rankings/current/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return TeamRankingData(team_number=team_number)
        return TeamRankingData(**response)

    def update_predicted_team_ranking_data(self, trd):
        # update the predicted ranking data on a specific team
        ref = "{0:s}/rankings/predicted".format(self.base_ref)
        if isinstance(trd, TeamRankingData):
            self.update_predicted_trd(trd.to_dict())
        elif isinstance(trd, dict):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(trd['team_number']), trd)
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating p trd {0:d}".format(['trd.team_number']))
                raise Exception("Error updating p trd {0:d}".format(trd['team_number']))
        else:
            logger.e("p trd variable is not a TeamRankingData object or dict")
            raise TypeError("p trd variable is not a TeamRankingData object or dict")

    def get_predicted_team_ranking_data(self, team_number):
        # get the predicted ranking data on a specific team
        ref = "{0:s}/rankings/predicted/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return TeamRankingData(team_number=team_number)
        return TeamRankingData(**response)

    def update_first_team_pick_ability(self, tpa):
        # update the first pick ability data for a specific team
        ref = "{0:s}/first_pick".format(self.base_ref)
        if isinstance(tpa, TeamPickAbility):
            self.update_first_team_pick_ability(tpa.to_dict())
        elif isinstance(tpa, dict):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(tpa['team_number']), tpa)
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating 1st tpa {0:d}".format(tpa['team_number']))
                raise Exception("Error updating 1st tpa {0:d}".format(tpa['team_number']))
        else:
            logger.e("1st tpa variable is not a TeamPickAbility object or dict")
            raise TypeError("1st tpa variable is not a TeamPickAbility object or dict")

    def get_first_team_pick_ability(self, team_number):
        # get the first pick ability data for a specific team
        ref = "{0:s}/first_pick/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return TeamPickAbility(team_number=team_number)
        return TeamPickAbility(**response)

    def update_second_team_pick_ability(self, tpa):
        # update the second pick ability data for a specific team
        ref = "{0:s}/second_pick".format(self.base_ref)
        if isinstance(tpa, TeamPickAbility):
            self.update_second_team_pick_ability(tpa.to_dict())
        elif isinstance(tpa, dict):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(tpa['team_number']), tpa)
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating 2nd tpa {0:d}".format(tpa['team_number']))
                raise Exception("Error updating 2nd tpa {0:d}".format(tpa['team_number']))
        else:
            logger.e("2nd tpa variable is not a TeamPickAbility object or dict")
            raise TypeError("2nd tpa variabel is not a TeamPickAbility object or dict")

    def get_second_team_pick_ability(self, team_number):
        # get the second pick ability data for a specific team
        ref = "{0:s}/second_pick/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return TeamPickAbility(team_number=team_number)
        return TeamPickAbility(**response)

    def update_third_team_pick_ability(self, tpa):
        # update the third pick ability data for a specific team
        ref = "{0:s}/third_pick".format(self.base_ref)
        if isinstance(tpa, TeamPickAbility):
            self.update_third_team_pick_ability(tpa.to_dict())
        elif isinstance(tpa, dict):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(tpa['team_number']), tpa)
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating 3rd tpa {0:d}".format(tpa['team_number']))
                raise Exception("Error updating 3rd tpa {0:d}".format(tpa['team_number']))
        else:
            logger.e("3rd tpa variable is not a TeamPickAbility object or dict")
            raise TypeError("3rd tpa variable is not a TeamPickAbility object or dict")

    def get_third_team_pick_ability(self, team_number):
        # get the third pick ability data for a specific team
        ref = "{0:s}/third_pick/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return TeamPickAbility(team_number=team_number)
        return TeamPickAbility(**response)

    def update_team(self, team):
        if isinstance(team, Team):
            self.update_team(team.to_dict())
        elif isinstance(team, dict):
            self.update_team_logistics(team['info'])
            self.update_team_pit_data(team['pit'])
            self.update_team_dt_feedback(team['drive_team_feedback'])
            self.update_team_calculated_data(team['calc'])
            self.update_current_team_ranking_data(team['current_ranking'])
            self.update_predicted_team_ranking_data(['team.predicted_ranking'])
            self.update_first_team_pick_ability(team['first_pick'])
            self.update_second_team_pick_ability(team['second_pick'])
            self.update_third_team_pick_ability(team['third_pick'])
            for tmd in team['completed_matches'].values():
                self.update_team_match_data(tmd)
        else:
            logger.e("team variable is not Team object or dict")
            raise TypeError("team variable is not Team object or dict")

    def get_team(self, team_number):
        team = Team()
        team.team_number = team_number
        team.info = self.get_team_logistics(team_number)
        team.pit = self.get_team_pit_data(team_number)
        team.drive_team_feedback = self.get_team_dt_feedback(team_number)
        team.calc = self.get_team_calculated_data(team_number)
        team.current_ranking = self.get_current_team_ranking_data(team_number)
        team.predicted_ranking = self.get_predicted_team_ranking_data(team_number)
        team.first_pick = self.get_first_team_pick_ability(team_number)
        team.second_pick = self.get_second_team_pick_ability(team_number)
        team.third_pick = self.get_third_team_pick_ability(team_number)
        for match_number in team.info.matches:
            team.completed_matches[match_number] = self.get_team_match_data(team_number=team_number,
                                                                            match_number=match_number)

    def get_team_numbers(self):
        ref = "{0:s}/info".format(self.base_ref)
        info_dict = self.get_python_object_from_firebase_location(ref)
        return [int(k) for k in info_dict.keys()]

    def get_teams(self):
        teams = []
        for team_number in self.get_team_numbers():
            teams.append(self.get_team(team_number))
        return teams

    def get_python_object_from_firebase_location(self, location):
        return utils.make_ascii_from_json(firebase.get(location, None))

    def cache(self):
        while True:
            try:
                data = json.dumps(firebase.get("/", None), indent=4)
                now = str(datetime.datetime.now())
                with open("./CachedFirebases/" + now + '.json', 'w') as f:
                    f.write(data)
                    f.close()
                    break
            except:
                logger.e("Error with caching firebase")
