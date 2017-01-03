import argparse
import time
import logging
import traceback
import signal
import sys
import json
import threading

from looper import Looper

from firebase_com import FirebaseCom
from the_blue_alliance import TheBlueAlliance
from crash_reporter import CrashReporter
from socket_server import SocketServer
from scouter_analysis import ScouterAnalysis

from data_models.match import Match
from data_models.alliance import Alliance
from data_models.team_logistics import TeamLogistics
from data_models.team_pit_data import TeamPitData
from data_models.team_ranking_data import TeamRankingData
from data_models.team_pick_ability import TeamPickAbility
from data_models.team_calculated_data import TeamCalculatedData
from data_models.low_level_stats import LowLevelStats

from calculators.team_calculation import TeamCalculation
from calculators.alliance_calculation import AllianceCalculation

from ourlogging import setup_logging

setup_logging(__file__)
logger = logging.getLogger(__name__)


class Server(Looper):
    DEFAULT_TIME_BETWEEN_CYCLES = 60 * 4  # 4 minutes
    DEFAULT_TIME_BETWEEN_CACHES = 60 * 60 * 1  # 1 hour

    def __init__(self, **kwargs):
        Looper.__init__(self)
        event_key = kwargs.get('event_key', "")
        logger.info("Event Key: {0:s}".format(event_key))
        self.event_key = event_key
        self.firebase = FirebaseCom(event_key)
        self.tba = TheBlueAlliance(event_key)
        self.event = None

        self.aggregate = kwargs.get('aggregate', False)

        if kwargs.get('crash_reporter', False):
            self.crash_reporter = CrashReporter(**kwargs)

        self.time_between_cycles = kwargs.get('time_between_cycles', self.DEFAULT_TIME_BETWEEN_CYCLES)
        self.time_between_caches = kwargs.get('time_between_caches', self.DEFAULT_TIME_BETWEEN_CACHES)

        self.set_loop_time(self.time_between_cycles)

        if kwargs.get('bluetooth', False):
            from bluetooth_server import BluetoothServer
            self.bluetooth = BluetoothServer()

        if kwargs.get('socket', False):
            self.socket = SocketServer()

        if kwargs.get('scouter_analysis', False):
            self.scouter_analysis = ScouterAnalysis(self.time_between_cycles, **kwargs)

        if kwargs.get('setup', False):
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

    def start(self):
        self.tstart()

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
            info = TeamLogistics()
            info.team_number = tba_team['team_number']
            info.nickname = tba_team['nickname']
            info.matches = team_matches[info.team_number]
            self.firebase.update_team_logistics(info)

            pit = TeamPitData()
            pit.team_number = info.team_number
            self.firebase.update_team_pit_data(pit)

            pick = TeamPickAbility()
            pick.team_number = info.team_number
            pick.nickname = info.nickname
            self.firebase.update_first_team_pick_ability(pick)
            self.firebase.update_second_team_pick_ability(pick)
            self.firebase.update_third_team_pick_ability(pick)
            logger.info("Team {0:d} added".format(info.team_number))

    def set_rankings(self, event_rankings):
        first = True
        for tba_ranking in list(event_rankings):
            if first:
                first = False
                continue
            tba_ranking_list = list(tba_ranking)
            ranking = TeamRankingData()
            ranking.team_number = int(tba_ranking_list[1])
            ranking.rank = int(tba_ranking_list[0])
            ranking.RPs = int(float(tba_ranking_list[2]))
            win_tie_lose = tba_ranking_list[7].split('-')
            ranking.wins = int(win_tie_lose[0])
            ranking.ties = int(win_tie_lose[2])
            ranking.loses = int(win_tie_lose[1])
            ranking.played = int(tba_ranking_list[8])
            self.firebase.update_current_team_ranking_data(ranking)
            logger.info("Added ranking for team {0:d}".format(ranking.team_number))

    def on_tstart(self):
        self.iteration = 1

        # initial run cache
        self.firebase.cache()
        self.time_since_last_cache = 0

        if hasattr(self, 'bluetooth'):
            self.bluetooth.start()

        if hasattr(self, 'socket'):
            self.socket.start()

        if hasattr(self, 'scouter_analysis'):
            self.scouter_analysis.start()

    def on_tloop(self):
        logger.info("Iteration {0:d}".format(self.iteration))
        if self.time_between_caches < self.time_since_last_cache:
            self.firebase.cache()
            self.time_since_last_cache = 0

        start_time = time.time()
        if self.aggregate:
            try:
                self.make_team_calculations()
                self.make_super_calculations()
                self.make_ranking_calculations()
                self.make_pick_list_calculations()
            except:
                if self.running:
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
            self.event = threading.Event()
            self.event.wait(timeout=self.time_between_cycles - time_taken)
            self.event = None
        self.time_since_last_cache += self.time_between_cycles
        self.iteration += 1

    def stop(self):
        if hasattr(self, 'bluetooth'):
            self.bluetooth.stop()
        if hasattr(self, 'socket'):
            self.socket.stop()
        if hasattr(self, 'scouter_analysis'):
            self.scouter_analysis.stop()
        Looper.stop(self)

    def make_team_calculations(self):
        # make low level calculations
        list_dict = {}
        for tmd in self.firebase.get_all_team_match_data().values():
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

                # strings don't have low level calculations
                if isinstance(tmd.__dict__[key], str):
                    continue

                # calculate the points score by this particular team in this match
                tmd.auto_points = 0
                tmd.teleop_points = 0
                tmd.endgame_points = 0
                tmd.total_points = tmd.auto_points + tmd.teleop_points + tmd.endgame_points

                # create lists for low level stats calculations
                if key is not list_dict[tmd.team_number]:
                    list_dict[tmd.team_number][key] = []
                list_dict[tmd.team_number][key].append(tmd.__dict__[key])
        # Create LowLevelStats
        for team_number, lists in iter(list_dict.items()):
            tcd = TeamCalculatedData()
            tcd.team_number = team_number
            for key, l in iter(lists.items()):
                if key in tcd.__dict__ and isinstance(tcd.__dict__[key], LowLevelStats):
                    tcd.__dict__[key] = LowLevelStats().from_list(l)
            self.firebase.update_team_calculated_data(tcd)
            logger.info("Updated Low Level Calculations for Team {0:d}".format(team_number))
        # high level calculations

    def make_super_calculations(self):
        for smd in self.firebase.get_all_super_match_data():
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
        # TODO: add in tie breaker to sort base on competition
        teams.sort(key=lambda x: x.predicted_ranking.RPs, reverse=True)
        rank = 1
        index = 0
        for team in teams:
            team.predicted_ranking = rank
            index += 1
            if index > 0 and team.predicted_ranking.RPs != teams[index - 1].predicted_ranking.RPs:
                rank = index + 1
            self.firebase.update_predicted_team_ranking_data(team.predicted_ranking)
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
            self.firebase.update_first_team_pick_ability(team.first_pick)
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
            self.firebase.update_second_team_pick_ability(team.second_pick)
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
            self.firebase.update_third_team_pick_ability(team.third_pick)
            logger.info("Updated third pick info for {0:d} on Firebase".format(team.team_number))


if __name__ == "__main__":
    # Collect command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--config", required=True, help="Config file with settings for the server")
    args = vars(ap.parse_args())

    f = open(args['config'])
    text = f.read()
    j = json.loads(text)

    server = Server(**j)

    def signal_handler(signal, frame):
        logging.info("Control-C caught stopping server at the end of this loop")
        server.stop()
        sys.exit()
    signal.signal(signal.SIGINT, signal_handler)
    server.start()
