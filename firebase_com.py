import json
import datetime
from firebase import firebase as fb
import utils

from threading import Lock as TLock
from multiprocessing import Lock as PLock

from DataModels.match import Match
from DataModels.team import Team
from DataModels.tid import TID
from DataModels.tpd import TPD
from DataModels.tmd import TMD
from DataModels.smd import SMD
from DataModels.tdtf import TDTF
from DataModels.tpa import TPA
from DataModels.trd import TRD
from DataModels.tcd import TCD

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
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(match.match_number), match.to_dict())
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating match {0:d}".format(match.match_number))
                raise Exception("Error updating match {0:d}".format(match.match_number))
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

    def update_tmd(self, tmd):
        # update the match data for a specific team that was in that match
        ref = "{0:s}/partial_match".format(self.base_ref)
        if isinstance(tmd, TMD):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}_{1:d}".format(tmd.match_number, tmd.team_number), tmd.to_dict())
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating tmd with match number {0:d} and team number {1:d}"
                         .format(tmd.match_number, tmd.team_number))
                raise Exception("Error updating tmd with match number {0:d} and team number {1:d}"
                                .format(tmd.match_number, tmd.team_number))
        elif isinstance(tmd, dict):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}_{1:d}".format(tmd['match_number'], tmd['team_number']), tmd)
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating tmd with match number{0:d} and team number {1:d}"
                         .format(tmd['match-Number'], tmd['team_number']))
                raise Exception("Error updating tmd with match {0:d} and team number {1:d}"
                                .format(tmd['match_number'], tmd['team_number']))
        else:
            logger.e("tmd variable not a TMD object or dict")
            raise TypeError("tmd variable not a TMD object or dict")

    def get_tmd(self, team_number, match_number):
        # get the match data for a specific team in a specific match
        ref = "{0:s}/partial_match/{1:d}_{2:d}".format(self.base_ref, match_number, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return TMD(team_number=team_number, match_number=match_number)
        return TMD(**response)

    def get_tmds(self):
        ref = "{0:s}/partial_match".format(self.base_ref)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return {}
        for key, tmd in iter(response.items()):
            response[key] = TMD(**tmd)
        return response

    def update_tpd(self, tpd):
        # update the pit data for a specific team
        ref = "{0:s}/pit".format(self.base_ref)
        if isinstance(tpd, TPD):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(tpd.team_number), tpd.to_dict())
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating tpd {0:d}".format(tpd.team_number))
                raise Exception("Error updating tpd {0:d}".format(tpd.team_number))
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
            logger.e("tpd variable not a TPD object or dict")
            raise TypeError("tpd variable not a TPD object or dict")

    def get_tpd(self, team_number):
        # get the pit data for a specific team
        ref = "{0:s}/pit/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return TPD(team_number=team_number)
        return TPD(**response)

    def update_smd(self, smd):
        # update the super scout data for a specific match
        ref = "{0:s}/super_match".format(self.base_ref)
        if isinstance(smd, SMD):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(smd.match_number), smd.to_dict())
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating smd {0:d}".format(smd.match_number))
                raise Exception("Error updating smd {0:d}".format(smd.match_number))
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
            logger.e("smd variable is not a SMD object or dict")
            raise TypeError("smd variable is not a SMD object or dict")

    def get_smd(self, match_number):
        # get the super scout data for a specific match
        ref = "{0:s}/super_match/{1:d}".format(self.base_ref, match_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return SMD(match_number=match_number)
        return SMD(**response)

    def get_smds(self):
        ref = "{0:s}/super_match".format(self.base_ref)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return []
        for key, value in iter(response.items()):
            response[key] = SMD(**value)
        return response

    def update_tdtf(self, tdtf):
        # update the drive team's feedback about a specific team
        ref = "{0:s}/feedback".format(self.base_ref)
        if isinstance(tdtf, TDTF):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(tdtf.team_number), tdtf.to_dict())
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating tdtf {0:d}".format(tdtf.team_number))
                raise Exception("Error updating tdtf {0:d}".format(tdtf.team_number))
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
            logger.e("tdtf variable is not a TDTF object or dict")
            raise TypeError("tdtf variable is not a TDTF object or dict")

    def get_tdtf(self, team_number):
        # get the drive team's feedback about a specific team
        ref = "{0:s}/feedback/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return TDTF(team_number=team_number)
        return TDTF(**response)

    def update_tid(self, tid):
        # update the logistics information about a specific team (nickname, match numbers, etc)
        ref = "{0:s}/info".format(self.base_ref)
        if isinstance(tid, TID):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(tid.team_number), tid.to_dict())
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating tid {0:d}".format(tid.team_number))
                raise Exception("Error updating tid {0:d}".format(tid.team_number))
        elif isinstance(tid, dict):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(tid['team_number']), tid)
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating tid {0:d}".format(tid['team_number']))
                raise Exception("Error updating tid {0:d}".format(tid['team_number']))
        else:
            logger.e("tid variable is not a TID object or dict")
            raise TypeError("tid variable is not a TID object or dict")

    def get_tid(self, team_number):
        # get the logistics information about a specific team (nickname, match numbers, etc)
        ref = "{0:s}/info/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return TID(team_number=team_number)
        return TID(**response)

    def update_tcd(self, tcd):
        # update the calculated data for a specific team
        ref = "{0:s}/calculated".format(self.base_ref)
        if isinstance(tcd, TCD):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(tcd.team_number), tcd.to_dict())
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating tcd {0:d}".format(tcd.team_number))
                raise Exception("Error updating tcd {0:d}".format(tcd.team_number))
        elif isinstance(tcd, dict):
            self.tlock.acquire()
            self.plock.acquire()
            return firebase.put(ref, "{0:d}".format(tcd['team_number']), tcd)
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating tcd {0:d}".format(tcd['team_number']))
                raise Exception("Error updating tcd {0:d}".format(tcd['team_number']))
        else:
            logger.e("tcd variable is not a TCD object or dict")
            raise TypeError("tcd variable is not a TCD object or dict")

    def get_tcd(self, team_number):
        # get the calculated data for a specific team
        ref = "{0:s}/calculated/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return TCD(team_number=team_number)
        return TCD(**response)

    def update_current_trd(self, trd):
        # update the current ranking data on a specific team
        ref = "{0:s}/rankings/current".format(self.base_ref)
        if isinstance(trd, TRD):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(trd.team_number), trd.to_dict())
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating c trd {0:d}".format(trd.team_number))
                raise Exception("Error updating c trd {0:d}".format(trd.team_number))
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
            logger.e("c trd variable is not a TRD object or dict")
            raise TypeError("c trd variable is not a TRD object or dict")

    def get_current_trd(self, team_number):
        # get the current ranking data on a specific team
        ref = "{0:s}/rankings/current/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return TRD(team_number=team_number)
        return TRD(**response)

    def update_predicted_trd(self, trd):
        # update the predicted ranking data on a specific team
        ref = "{0:s}/rankings/predicted".format(self.base_ref)
        if isinstance(trd, TRD):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(trd.team_number), trd.to_dict())
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating p trd {0:d}".format(trd.team_number))
                raise Exception("Error updating p trd {0:d}".format(trd.team_number))
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
            logger.e("p trd variable is not a TRD object or dict")
            raise TypeError("p trd variable is not a TRD object or dict")

    def get_predicted_trd(self, team_number):
        # get the predicted ranking data on a specific team
        ref = "{0:s}/rankings/predicted/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return TRD(team_number=team_number)
        return TRD(**response)

    def update_first_tpa(self, tpa):
        # update the first pick ability data for a specific team
        ref = "{0:s}/first_pick".format(self.base_ref)
        if isinstance(tpa, TPA):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(tpa.team_number), tpa.to_dict())
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating 1st tpa {0:d}".format(tpa.team_number))
                raise Exception("Error updating 1st tpa {0:d}".format(tpa.team_number))
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
            logger.e("1st tpa variable is not a TPA object or dict")
            raise TypeError("1st tpa variable is not a TPA object or dict")

    def get_first_tpa(self, team_number):
        # get the first pick ability data for a specific team
        ref = "{0:s}/first_pick/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return TPA(team_number=team_number)
        return TPA(**response)

    def update_second_tpa(self, tpa):
        # update the second pick ability data for a specific team
        ref = "{0:s}/second_pick".format(self.base_ref)
        if isinstance(tpa, TPA):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(tpa.team_number), tpa.to_dict())
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating 2nd tpa {0:d}".format(tpa.team_number))
                raise Exception("Error updating 2nd tpa {0:d}".format(tpa.team_number))
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
            logger.e("2nd tpa variable is not a TPA object or dict")
            raise TypeError("2nd tpa variabel is not a TPA object or dict")

    def get_second_tpa(self, team_number):
        # get the second pick ability data for a specific team
        ref = "{0:s}/second_pick/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return TPA(team_number=team_number)
        return TPA(**response)

    def update_third_tpa(self, tpa):
        # update the third pick ability data for a specific team
        ref = "{0:s}/third_pick".format(self.base_ref)
        if isinstance(tpa, TPA):
            self.tlock.acquire()
            self.plock.acquire()
            success = firebase.put(ref, "{0:d}".format(tpa.team_number), tpa.to_dict())
            self.tlock.release()
            self.plock.release()
            if not success:
                logger.e("Error updating 3rd tpa {0:d}".format(tpa.team_number))
                raise Exception("Error updating 3rd tpa {0:d}".format(tpa.team_number))
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
            logger.e("3rd tpa variable is not a TPA object or dict")
            raise TypeError("3rd tpa variable is not a TPA object or dict")

    def get_third_tpa(self, team_number):
        # get the third pick ability data for a specific team
        ref = "{0:s}/third_pick/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        if response is None:
            return TPA(team_number=team_number)
        return TPA(**response)

    def update_team(self, team):
        if isinstance(team, Team):
            self.update_tid(team.info)
            self.update_tpd(team.pit)
            self.update_tdtf(team.drive_team_feedback)
            self.update_tcd(team.calc)
            self.update_current_trd(team.current_ranking)
            self.update_predicted_trd(team.predicted_ranking)
            self.update_first_tpa(team.first_pick)
            self.update_second_tpa(team.second_pick)
            self.update_third_tpa(team.third_pick)
            for tmd in team.completed_matches.values():
                self.update_tmd(tmd)
        elif isinstance(team, dict):
            self.update_tid(team['info'])
            self.update_tpd(team['pit'])
            self.update_tdtf(team['drive_team_feedback'])
            self.update_tcd(team['calc'])
            self.update_current_trd(team['current_ranking'])
            self.update_predicted_trd(['team.predicted_ranking'])
            self.update_first_tpa(team['first_pick'])
            self.update_second_tpa(team['second_pick'])
            self.update_third_tpa(team['third_pick'])
            for tmd in team['completed_matches'].values():
                self.update_tmd(tmd)
        else:
            logger.e("team variable is not Team object or dict")
            raise TypeError("team variable is not Team object or dict")

    def get_team(self, team_number):
        team = Team()
        team.team_number = team_number
        team.info = self.get_tid(team_number)
        team.pit = self.get_tpd(team_number)
        team.drive_team_feedback = self.get_tdtf(team_number)
        team.calc = self.get_tcd(team_number)
        team.current_ranking = self.get_current_trd(team_number)
        team.predicted_ranking = self.get_predicted_trd(team_number)
        team.first_pick = self.get_first_tpa(team_number)
        team.second_pick = self.get_second_tpa(team_number)
        team.third_pick = self.get_third_tpa(team_number)
        for match_number in team.info.matches:
            team.completed_matches[match_number] = self.get_tmd(team_number=team_number,
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
