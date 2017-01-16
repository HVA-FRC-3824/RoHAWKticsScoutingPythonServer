import argparse
import time
import logging
import traceback
import signal
import sys
import json
import threading
import scipy.stats as stats
from threading import Event
from looper import Looper
from functools import cmp_to_key

from firebase_com import FirebaseCom
from the_blue_alliance import TheBlueAlliance
from crash_reporter import CrashReporter
from socket_server import SocketServer
from scout_analysis import ScoutAnalysis

from data_models.match import Match
from data_models.alliance import Alliance
from data_models.team_logistics import TeamLogistics
from data_models.team_pit_data import TeamPitData
from data_models.team_ranking_data import TeamRankingData
from data_models.team_pick_ability import TeamPickAbility
from data_models.team_calculated_data import TeamCalculatedData
from data_models.low_level_stats import LowLevelStats

from calculators.team_calculator import TeamCalculator
from calculators.alliance_calculator import AllianceCalculator

from ourlogging import setup_logging

setup_logging(__file__)
logger = logging.getLogger(__name__)


class Server(Looper):
    '''Main server class that interprets the config file and starts various threads'''
    DEFAULT_TIME_BETWEEN_CYCLES = 60 * 4  # 4 minutes
    DEFAULT_TIME_BETWEEN_CACHES = 60 * 60 * 1  # 1 hour

    def __init__(self, **kwargs):
        ''' Initialization of all the server components based on the config

        Kwargs:
            The config json converted to a `dict`
        '''
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
            self.scout_analysis = ScoutAnalysis(self.time_between_cycles, **kwargs)

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
        '''Starts the main thread loop'''
        self.event = None
        self.running = True
        self.on_tstart()
        while self.running:
            start_time = time.time()
            self.on_tloop()
            end_time = time.time()
            delta_time = end_time - start_time
            if self.loop_time - delta_time > 0 and self.running:
                self.event = Event()
                self.event.wait(timeout=self.loop_time - delta_time)
                self.event = None

    def set_matches(self, event_matches):
        '''Converts the match information pulled from `The Blue Alliance <thebluealliance.com>`_ into :class:`Match`

        Args:
            event_matches (dict): The match information pulled from `The Blue Alliance <thebluealliance.com>`_

        Returns:
                A `dict` contain all the match numbers for each team
        '''
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
        '''Converts the team information from `The Blue Alliance <thebluealliance.com>`_
           to :class:`TeamLogistics`.

            Converts the team information from `The Blue Alliance <thebluealliance.com>`_
            to :class:`TeamLogistics`. Also, sets the match numbers for each team
            from the result of :func:`set_matches`

        Args:
            event_teams (dict): The team information from `The Blue Alliance <thebluealliance.com>`_

            team_matches (dict): The match numbers for each team

        '''
        team_logistics = []

        for tba_team in event_teams:
            info = TeamLogistics()
            info.team_number = tba_team['team_number']
            info.nickname = tba_team['nickname']
            info.matches = team_matches[info.team_number]
            team_logistics.append(info)

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

        min_matches = 100  # Each team should always have less than 100 matches
        for team in team_logistics:
            if len(team.matches) < min_matches:
                min_matches = len(team_matches)

        for team in team_logistics:
            if len(team.matches) > min_matches:
                team.surrogate_match_number = team.matches[3]
            self.firebase.update_team_logistics(info)

    def set_rankings(self, event_rankings):
        '''Convert the ranking information from `The Blue Alliance <thebluealliance.com>`_
           to the :class:`TeamRankingData`
        '''
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
        '''Runs before the main loop and starts the threads for :class:`BluetoothServer`,
           :class:`SocketServer`, and :class:`ScouterAnalysis` based on the config. Also,
           caches the firebase data.
        '''
        self.iteration = 1

        # initial run cache
        self.firebase.cache()
        self.time_since_last_cache = 0

        if hasattr(self, 'bluetooth'):
            self.bluetooth.start()

        if hasattr(self, 'socket'):
            self.socket.start()

        if hasattr(self, 'scout_analysis'):
            self.scout_analysis.start()

    def on_tloop(self):
        '''Runs on each iteration of the main loop and aggregates the data.'''
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
        '''Stops all threads'''
        if hasattr(self, 'bluetooth'):
            self.bluetooth.stop()
        if hasattr(self, 'socket'):
            self.socket.stop()
        if hasattr(self, 'scout_analysis'):
            self.scout_analysis.stop()
        Looper.stop(self)

    def make_team_calculations(self):
        '''Make all the calculations from the :class:`TeamMatchData`'''
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
        '''Makes all the calculations from the :class:`SuperMatchData`'''
        lists = {}
        tcd = self.firebase.get_team_calculated_data(-1)
        for key in tcd.__dict__.keys():
            if 'zscore' in key:
                lists[key[6:]] = {}

        # get match rankings from super match data and put in lists for averaging
        for smd in self.firebase.get_all_super_match_data():
            for key, value in smd.__dict__.items():
                if 'blue' in key:
                    key = key[5:]
                elif 'red' in key:
                    key = key[4:]

                if key in lists:
                    for i, team_number in enumerate(value):
                        if team_number not in lists[key]:
                            lists[key][team_number] = []
                        match_rank = 3 - i
                        if match_rank == 3:
                            match_rank = 4
                        lists[key][team_number].append(match_rank)

        zscore_components = {}
        for key in lists:
            zscore_components[key] = {}
            zscore_components[key]['team_numbers'] = []
            zscore_components[key]['averages'] = []
            zscore_components[key]['zscore'] = []
            zscore_components[key]['rank'] = []
            for team_number in lists[key]:
                average = 0.0
                for value in lists[key][team_number]:
                    average += value
                zscore_components[key]['team_number'].append(team_number)
                zscore_components[key]['averages'].append(average / len(list[key][team_number]))
            zscore_components[key]['zscores'] = stats.zscore(zscore_components[key]['averages'])

            # Create list for sorting
            teams = []
            for i in range(len(zscore_components[key]['team_number'])):
                team = {}
                team['team_number'] = zscore_components[key]['team_number'][i]
                team['zscore'] = zscore_components[key]['zscores'][i]
            # Make the zscore negative for sorting so larger numbers are at the beginning
            teams = sorted(teams, key=lambda team: -team['zscore'])

            # add calculations to firebase
            for i, team in enumerate(teams):
                firebase_team = self.firebase.get_team_calculated_data(team['team_number'])
                firebase_team.__dict__["zscore_"+key] = team['zscore']
                firebase_team.__dict__["rank_"+key] = i + 1
                self.firebase.update_team_calculated_data(firebase_team)

    def make_ranking_calculations(self):
        '''Pulls the current rankings from `The Blue Alliance <thebluealliance.com>`_
           and predicts the final rankings
        '''
        # Current Rankings
        event_rankings = self.tba.get_event_rankings()
        self.set_rankings(event_rankings)
        logger.info("Updated current rankings on Firebase")

        # Predicted Rankings
        teams = []
        for team in self.firebase.get_teams():
            team.predicted_ranking.played = len(team.info.match_numbers)

            team.predicted_ranking.RPs = team.current_ranking.RPs
            team.predicted_ranking.wins = team.current_ranking.wins
            team.predicted_ranking.ties = team.current_ranking.ties
            team.predicted_ranking.loses = team.current_ranking.loses
            team.predicted_ranking.first_tie_breaker = team.current_ranking.first_tie_breaker
            team.predicted_ranking.second_tie_breaker = team.current_ranking.second_tie_breaker

            for index in range(len(team.completed_matches), len(team.info.match_numbers)):
                match = self.firebase.get_match(team.info.match_numbers[index])

                # If match is a surrogate match ignore it
                if match.match_number == team.info.surrogate_match_number:
                    continue

                if match.is_blue(team.team_number):
                    ac = AllianceCalculator(Alliance(*match.teams[0:2]))
                    opp = AllianceCalculator(Alliance(*match.teams[3:5]))
                else:
                    ac = AllianceCalculator(Alliance(*match.teams[3:5]))
                    opp = AllianceCalculator(Alliance(*match.teams[0:2]))

                if ac.win_probability_over(opp) > 0.5:
                    team.predicted_ranking.wins += 1
                    team.predicted_ranking.RPs += 2
                elif opp.win_probabiliy_over(ac) > 0.5:
                    team.predicted_ranking.loses += 1
                else:
                    team.predicted_ranking.ties += 1
                    team.predicted_ranking.RPs += 1

                team.predicted_ranking.first_tie_breaker += ac.predicted_score()
                teams.predicted_ranking.second_tie_breaker += ac.predicted_auto_score()
            teams.append(team)

        # Sort for ranking
        def ranking_cmp(team1, team2):
            if team1.predicted_ranking.RPs > team2.predicted_ranking.RPs:
                return 1
            elif team1.predicted_ranking.RPs < team2.predicted_ranking.RPs:
                return -1
            else:  # tie
                if team1.predicted_ranking.first_tie_breaker > team2.predicted_ranking.first_tie_breaker:
                    return 1
                elif team1.predicted_ranking.first_tie_breaker < team2.predicted_ranking.first_tie_breaker:
                    return -1
                else:
                    if team1.predicted_ranking.second_tie_breaker > team2.predicted_ranking.second_tie_breaker:
                        return 1
                    elif team1.predicted_ranking.second_tie_breaker < team2.predicted_ranking.second_tie_breaker:
                        return -1
                    else:
                        return 0  # Really we should never get here

        teams.sort(key=cmp_to_key(ranking_cmp), reverse=True)
        for rank, team in enumerate(teams):
            team.predicted_ranking = rank + 1
            self.firebase.update_predicted_team_ranking_data(team.predicted_ranking)
            logger.info("Updated predicted ranking for {0:d} on Firebase".format(team.team_number))

    def make_pick_list_calculations(self):
        '''Make calculations for :class:`TeamPickAbility` based on :class:`TeamMatchData`,
        :class:`SuperMatchData`, and :class:`TeamCalculatedData`
        '''
        for team in self.firebase.get_teams().values():
            tc = TeamCalculator(team)

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
        '''Catches control-c and cleanly shuts down the server'''
        logging.info("Control-C caught. Cleanly shutting down the server.")
        server.stop()
        sys.exit()
    signal.signal(signal.SIGINT, signal_handler)
    server.start()
