import json
import datetime
from firebase import firebase as fb
import utils

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

# TODO: add authentication

(secret, url) = ('TSkriBv7Z81MpfvsUM332f4HmtoAOjSUiN5xRLAb',
                 'https://rohawktics-scouting-2017.firebaseio.com/')

# auth = fb.FirebaseAuthentication(secret, "", True, True)

firebase = fb.FirebaseApplication(url)


class FirebaseCom:
    def __init__(self, event_id):
        self.matches = []
        self.teams = []
        self.event_id = event_id
        self.base_ref = "/{0:s}".format(self.event_id)

    def update_match(self, match):
        # update logistics information about a match (who was in it, score breakdown, etc)
        ref = "{0:s}/schedule".format(self.base_ref)
        return firebase.put(ref, "{0:d}".format(match.match_number), match.to_dict())

    def get_match(self, match_number):
        # get logistics information about a match (who was in it, score breakdown, etc)
        ref = "{0:s}/schedule/{1:d}".format(self.base_ref, match_number)
        response = self.get_python_object_from_firebase_location(ref)
        return Match(**response)

    def update_tmd(self, tmd):
        # update the match data for a specific team that was in that match
        ref = "{0:s}/partial_match".format(self.base_ref)
        return firebase.put(ref, "{0:d}_{1:d}".format(tmd.match_number, tmd.team_number), tmd.to_dict())

    def get_tmd(self, team_number, match_number):
        # get the match data for a specific team in a specific match
        ref = "{0:s}/partial_match/{1:d}_{2:d}".format(self.base_ref, match_number, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        return TMD(**response)

    def get_tmds(self):
        ref = "{0:s}/partial_match".format(self.base_ref)
        response = self.get_python_object_from_firebase_location(ref)
        for key, tmd in iter(response.items()):
            response[key] = TMD(**tmd)
        return response

    def update_tpd(self, tpd):
        # update the pit data for a specific team
        ref = "{0:s}/pit".format(self.base_ref)
        return firebase.put(ref, "{0:d}".format(tpd.team_number), tpd.to_dict())

    def get_tpd(self, team_number):
        # get the pit data for a specific team
        ref = "{0:s}/pit/{0:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        return TPD(**response)

    def update_smd(self, smd):
        # update the super scout data for a specific match
        ref = "{0:s}/super_match".format(self.base_ref)
        return firebase.put(ref, "{0:d}".format(smd.match_number), smd.to_dict())

    def get_smd(self, match_number):
        # get the super scout data for a specific match
        ref = "{0:s}/super_match/{1:d}".format(self.base_ref, match_number)
        response = self.get_python_object_from_firebase_location(ref)
        return SMD(**response)

    def update_tdtf(self, tdtf):
        # update the drive team's feedback about a specific team
        ref = "{0:s}/feedback".format(self.base_ref)
        return firebase.put(ref, "{0:d}".format(tdtf.team_number), tdtf.to_dict())

    def get_tdtf(self, team_number):
        # get the drive team's feedback about a specific team
        ref = "{0:s}/feedback/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        return TDTF(**response)

    def update_tid(self, tid):
        # update the logistics information about a specific team (nickname, match numbers, etc)
        ref = "{0:s}/info".format(self.base_ref)
        return firebase.put(ref, "{0:d}".format(tid.team_number), tid.to_dict())

    def get_tid(self, team_number):
        # get the logistics information about a specific team (nickname, match numbers, etc)
        ref = "{0:s}/info/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        return TID(**response)

    def update_tcd(self, tcd):
        # update the calculated data for a specific team
        ref = "{0:s}/calculated".format(self.base_ref)
        return firebase.put(ref, "{0:d}".format(tcd.team_number), tcd.to_dict())

    def get_tcd(self, team_number):
        # get the calculated data for a specific team
        ref = "{0:s}/calculated/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        return TCD(**response)

    def update_current_trd(self, trd):
        # update the current ranking data on a specific team
        ref = "{0:s}/rankings/current".format(self.base_ref)
        return firebase.put(ref, "{0:d}".format(trd.team_number), trd.to_dict())

    def get_current_trd(self, team_number):
        # get the current ranking data on a specific team
        ref = "{0:s}/rankings/current/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        return TRD(**response)

    def update_predicted_trd(self, trd):
        # update the predicted ranking data on a specific team
        ref = "{0:s}/rankings/predicted".format(self.base_ref)
        return firebase.put(ref, "{0:d}".format(trd.team_number), trd.to_dict())

    def get_predicted_trd(self, team_number):
        # get the predicted ranking data on a specific team
        ref = "{0:s}/rankings/predicted/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        return TRD(**response)

    def update_first_tpa(self, tpa):
        # update the first pick ability data for a specific team
        ref = "{0:s}/first_pick".format(self.base_ref)
        return firebase.put(ref, "{0:d}".format(tpa.team_number), tpa.to_dict())

    def get_first_tpa(self, team_number):
        # get the first pick ability data for a specific team
        ref = "{0:s}/first_pick/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        return TPA(**response)

    def update_second_tpa(self, tpa):
        # update the second pick ability data for a specific team
        ref = "{0:s}/second_pick".format(self.base_ref)
        return firebase.put(ref, "{0:d}".format(tpa.team_number), tpa.to_dict())

    def get_second_tpa(self, team_number):
        # get the second pick ability data for a specific team
        ref = "{0:s}/second_pick/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        return TPA(**response)

    def update_third_tpa(self, tpa):
        # update the third pick ability data for a specific team
        ref = "{0:s}/third_pick".format(self.base_ref)
        return firebase.put(ref, "{0:d}".format(tpa.team_number), tpa.to_dict())

    def get_third_tpa(self, team_number):
        # get the third pick ability data for a specific team
        ref = "{0:s}/third_pick/{1:d}".format(self.base_ref, team_number)
        response = self.get_python_object_from_firebase_location(ref)
        return TPA(**response)

    def update_team(self, team):
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
            team.completed_matches[match_number] = self.get_tmd(team_number)

    def get_python_object_from_firebase_location(self, location):
        return utils.make_ascii_from_json(firebase.get(location, None))

    def cache_firebase(self):
        while True:
            try:
                data = json.dumps(firebase.get("/", None))
                now = str(datetime.datetime.now())
                with open("./CachedFirebases/" + now + '.json', 'w') as f:
                    f.write(data)
                    f.close()
                    break
            except:
                pass
