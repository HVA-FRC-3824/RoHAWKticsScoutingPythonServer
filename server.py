import argparse
import time
import logging
import traceback
import signal
import sys

from firebase_com import FirebaseCom
from the_blue_alliance import TheBlueAlliance
from crash_reporter import CrashReporter

from DataModels.match import Match
from DataModels.alliance import Alliance
from DataModels.tid import TID
from DataModels.tpd import TPD
from DataModels.trd import TRD
from DataModels.tpa import TPA
from DataModels.tcd import TCD
from DataModels.low_level_stats import LowLevelStats

from Calculators.team_calculation import TeamCalculation
from Calculators.alliance_calculation import AllianceCalculation

from ourlogging import setup_logging

setup_logging(__file__)
logger = logging.getLogger(__name__)


class Server:
    DEFAULT_TIME_BETWEEN_CYCLES = 60 * 4  # 4 minutes
    DEFAULT_TIME_BETWEEN_CACHES = 60 * 60 * 1  # 1 hour

    def __init__(self, event_key, setup, tbc, tbca, rc):
        logger.info("Event Key: {0:s}".format(event_key))
        self.event_key = event_key
        self.firebase = FirebaseCom(event_key)
        self.tba = TheBlueAlliance(event_key)

        if rc:
            self.crash_reporter = CrashReporter()

        if tbc is not None:
            self.time_between_cycles = tbc
        else:
            self.time_between_cycles = self.DEFAULT_TIME_BETWEEN_CYCLES

        if tbca is not None:
            self.time_between_caches = tbca
        else:
            self.time_between_caches = self.DEFAULT_TIME_BETWEEN_CACHES

        if setup:
            logger.info("Setting up database...")
            event_matches = self.tba.get_event_matches()
            team_matches = self.set_matches(event_matches)
            logger.info("Added matches to Firebase")

            event_teams = self.tba.get_event_teams()
            self.set_teams(event_teams, team_matches)
            logger.info("Added teams to Firebase")

            event_rankings = self.tba.get_event_rankings()
            self.set_rankings(event_rankings)
            logger.info("Added rankings to Firebase")

    def set_matches(self, event_matches):
        team_matches = {}
        for tba_match in event_matches:
            if tba_match['comp_level'] != "qm":
                continue

            match = Match()
            match.match_number = tba_match['match_number']
            for color in ['blue', 'red']:
                for team_key in tba_match['alliances'][color]['teams']:
                    match.teams.append(int(team_key[3:]))
                match.scores.append(int(tba_match['alliances'][color]['score']))

            for team_number in match.teams:
                if team_number not in team_matches:
                    team_matches[team_number] = []
                team_matches[team_number].append(match.match_number)
            self.firebase.update_match(match)
            logger.info("Match {0:d} added".format(match.match_number))
        return team_matches

    def set_teams(self, event_teams, team_matches):
        for tba_team in event_teams:
            info = TID()
            info.team_number = tba_team['team_number']
            info.nickname = tba_team['nickname']
            info.matches = team_matches[info.team_number]
            self.firebase.update_tid(info)

            pit = TPD()
            pit.team_number = info.team_number
            self.firebase.update_tpd(pit)

            pick = TPA()
            pick.team_number = info.team_number
            pick.nickname = info.nickname
            self.firebase.update_first_tpa(pick)
            self.firebase.update_second_tpa(pick)
            self.firebase.update_third_tpa(pick)
            logger.info("Team {0:d} added".format(info.team_number))

    def set_rankings(self, event_rankings):
        first = True
        for tba_ranking in list(event_rankings):
            if first:
                first = False
                continue
            tba_ranking_list = list(tba_ranking)
            ranking = TRD()
            ranking.team_number = int(tba_ranking_list[1])
            ranking.rank = int(tba_ranking_list[0])
            ranking.RPs = int(float(tba_ranking_list[2]))
            win_tie_lose = tba_ranking_list[7].split('-')
            ranking.wins = int(win_tie_lose[0])
            ranking.ties = int(win_tie_lose[2])
            ranking.loses = int(win_tie_lose[1])
            ranking.played = int(tba_ranking_list[8])
            self.firebase.update_current_trd(ranking)
            logger.info("Added ranking for team {0:d}".format(ranking.team_number))

    def run(self):
        self.stopped = False
        iteration = 1

        # initial run cache
        self.firebase.cache()
        time_since_last_cache = 0
        while not self.stopped:
            logger.info("Iteration {0:d}".format(iteration))
            if self.time_between_caches < time_since_last_cache:
                self.firebase.cache()
                time_since_last_cache = 0

            start_time = time.time()
            try:
                self.make_team_calculations()
                self.make_super_calculations()
                self.make_ranking_calculations()
                self.make_pick_list_calculations()
            except:
                if not self.stopped:
                    logger.error("Crash")
                    logger.error(traceback.format_exc())
                    if hasattr(self, 'crash_reporter'):
                        logger.error("Reporting crash")
                        try:
                            self.crash_reporter.report_server_crash(traceback.format_exc())
                        # weird exception that doesn't stop the text
                        except:
                            pass
            end_time = time.time()
            time_taken = end_time - start_time
            logger.info("Iteration Ended")
            logger.info("Time taken: {0:f}s".format(time_taken))
            if self.time_between_cycles - time_taken > 0:
                time.sleep(self.time_between_cycles - time_taken)
            time_since_last_cache += self.time_between_cycles
            iteration += 1
        sys.exit()

    def stop(self):
        self.stopped = True

    def make_team_calculations(self):
        # make low level calculations
        list_dict = {}
        for tmd in self.firebase.get_tmds().values():
            if tmd.team_number not in list_dict:
                list_dict[tmd.team_number] = {}
            for key in tmd.__dict__.keys():
                if key == 'team_number':
                    continue

                # Convert firebase booleans
                if tmd.__dict__[key] == 'true':
                    tmd.__dict__[key] = True
                elif tmd.__dict__[key] == 'false':
                    tmd.__dict__[key] = False

                if isinstance(tmd.__dict__[key], str):
                    continue
                if key is not list_dict[tmd.team_number]:
                    list_dict[tmd.team_number][key] = []
                list_dict[tmd.team_number][key].append(tmd.__dict__[key])
        for team_number, lists in iter(list_dict.items()):
            tcd = TCD()
            tcd.team_number = team_number
            for key, l in iter(lists.items()):
                if key in tcd.__dict__ and isinstance(tcd.__dict__[key], LowLevelStats):
                    tcd.__dict__[key] = LowLevelStats().from_list(l)
            self.firebase.update_tcd(tcd)
            logger.info("Updated Low Level Calculations for Team {0:d}".format(team_number))
        # high level calculations

    def make_super_calculations(self):
        for smd in self.firebase.get_smds():
            pass

    def make_ranking_calculations(self):
        # Current Rankings
        event_rankings = self.tba.get_event_rankings()
        self.set_rankings(event_rankings)
        logger.info("Updated current rankings on Firebase")

        # Predicted Rankings
        teams = []
        for team in self.firebase.get_teams():
            print(team.team_number)
            team.predicted_ranking.played = len(team.info.match_numbers)

            team.predicted_ranking.RPs = team.current_ranking.RPs
            team.predicted_ranking.wins = team.current_ranking.wins
            team.predicted_ranking.ties = team.current_ranking.ties
            team.predicted_ranking.loses = team.current_ranking.loses

            for index in range(len(team.completed_matches), len(team.info.match_numbers)):
                match = self.firebase.get_match(team.info.match_numbers[index])
                print(match.match_number)
                if match.is_blue(team.team_number):
                    ac = AllianceCalculation(Alliance(*match.teams[0:2]))
                    opp = AllianceCalculation(Alliance(*match.teams[3:5]))
                else:
                    ac = AllianceCalculation(Alliance(*match.teams[3:5]))
                    opp = AllianceCalculation(Alliance(*match.teams[0:2]))

                if ac.win_probability_over(opp) > 0.5:
                    team.predicted_ranking.wins += 1
                    team.predicted_ranking.RPs += 2
                elif opp.win_probabiliy_over(ac) > 0.5:
                    team.predicted_ranking.loses += 1
                else:
                    team.predicted_ranking.ties += 1
                    team.predicted_ranking.RPs += 1
            teams.append(team)
        # Sort for ranking
        # TODO: add in tie breaker to sort
        teams.sort(key=lambda x: x.predicted_ranking.RPs, reverse=True)
        rank = 1
        index = 0
        for team in teams:
            team.predicted_ranking = rank
            index += 1
            if index > 0 and team.predicted_ranking.RPs != teams[index - 1].predicted_ranking.RPs:
                rank = index + 1
            self.firebase.update_predicted_trd(team.predicted_ranking)
            logger.info("Updated predicted ranking for {0:d} on Firebase".format(team.team_number))

    def make_pick_list_calculations(self):
        for team in self.firebase.get_teams().values():
            tc = TeamCalculation(team)

            # First Pick
            team.first_pick.pick_ability = tc.first_pick_ability()
            team.robot_picture_filepath = team.pit.robot_picture_filepath
            team.first_pick.yellow_card = team.calc.yellow_card.total > 0
            team.first_pick.red_card = team.calc.red_card.total > 0
            team.stopped_moving = team.calc.stopped_moving.total > 1
            team.first_pick.top_line = "PA: {0:f}".format(team.first_pick.pick_ability)
            team.first_pick.second_line = "".format()
            team.first_pick.third_line = "".format()
            self.firebase.update_first_tpa(team.first_pick)
            logger.info("Updated first pick info for {0:d} on Firebase".format(team.team_number))

            # Second Pick
            team.second_pick.pick_ability = tc.second_pick_ability()
            team.robot_picture_filepath = team.pit.robot_picture_filepath
            team.second_pick.yellow_card = team.calc.yellow_card.total > 0
            team.second_pick.red_card = team.calc.red_card.total > 0
            team.stopped_moving = team.calc.stopped_moving.total > 1
            team.second_pick.top_line = "PA: {0:f}".format(team.second_pick.pick_ability)
            team.second_pick.second_line = "".format()
            team.second_pick.third_line = "".format()
            self.firebase.update_second_tpa(team.second_pick)
            logger.info("Updated second pick info for {0:d} on Firebase".format(team.team_number))

            # Third Pick
            team.third_pick.pick_ability = tc.third_pick_ability()
            team.robot_picture_filepath = team.pit.robot_picture_filepath
            team.third_pick.yellow_card = team.calc.yellow_card.total > 0
            team.third_pick.red_card = team.calc.red_card.total > 0
            team.stopped_moving = team.calc.stopped_moving.total > 1
            team.third_pick.top_line = "PA: {0:f}".format(team.third_pick.pick_ability)
            team.third_pick.second_line = "".format()
            team.third_pick.third_line = "".format()
            self.firebase.update_third_tpa(team.third_pick)
            logger.info("Updated third pick info for {0:d} on Firebase".format(team.team_number))


if __name__ == "__main__":
    # Collect command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-e", "--event_key", required=True, help="Event key for The Blue Alliance")
    ap.add_argument("-l", "--log_level", required=False, help="The level threshold for the logger")
    ap.add_argument("-s", "--setup", required=False, action="store_true",
                    help="Setup the database for this event")
    ap.add_argument("-t", "--time_between_cycles", required=False, help="Time between cycles")
    ap.add_argument("-r", "--report_crash", required=False, action="store_true",
                    help="Report whenever there is a crash through email and text")
    ap.add_argument("-c", "--time_between_caches", required=False, help="Time between backup caching")
    args = vars(ap.parse_args())

    server = Server(args['event_key'], args['setup'], args['time_between_cycles'],
                    args['time_between_caches'], args['report_crash'])

    def signal_handler(signal, frame):
        server.stop()
        sys.exit()
        # logger.info("Control-C caught stopping server at the end of this loop")
    signal.signal(signal.SIGINT, signal_handler)
    server.run()
