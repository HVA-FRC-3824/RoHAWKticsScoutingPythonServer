import logging
import re
import scipy.stats as stats

from constants import Constants

from data_models.gear import Gear
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

from functools import cmp_to_key

from ourlogging import setup_logging

setup_logging(__file__)
logger = logging.getLogger(__name__)


class Aggregator:
    @staticmethod
    def set_matches(firebase, event_matches):
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
            firebase.update_match(match)
            logger.info("Match {0:d} added".format(match.match_number))
        return team_matches

    @staticmethod
    def set_teams(firebase, event_teams, team_matches):
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
            firebase.update_team_pit_data(pit)

            pick = TeamPickAbility()
            pick.team_number = info.team_number
            pick.nickname = info.nickname
            firebase.update_first_team_pick_ability(pick)
            firebase.update_second_team_pick_ability(pick)
            firebase.update_third_team_pick_ability(pick)
            logger.info("Team {0:d} added".format(info.team_number))

        min_matches = 100  # Each team should always have less than 100 matches
        for team in team_logistics:
            if len(team.matches) < min_matches:
                min_matches = len(team_matches)

        for team in team_logistics:
            if len(team.matches) > min_matches:
                team.surrogate_match_number = team.matches[3]
            firebase.update_team_logistics(info)

    @staticmethod
    def set_rankings(firebase, event_rankings):
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
            firebase.update_current_team_ranking_data(ranking)
            logger.info("Added ranking for team {0:d}".format(ranking.team_number))

    @staticmethod
    def make_team_calculations(firebase):
        '''Make all the calculations from the :class:`TeamMatchData`'''
        # make low level calculations
        list_dict = {}
        constants = Constants()
        pattern = re.compile(r"< (\d+)s")
        for tmd in firebase.get_all_team_match_data().values():
            if tmd.team_number not in list_dict:
                list_dict[tmd.team_number] = {}

            # calculate the points score by this particular team in this match
            tmd.auto_points = 0
            tmd.auto_points += 5 if tmd.auto_baseline else 0
            tmd.teleop_points = 0

            auto_gears_placed = 0
            for gear in tmd.auto_gears:
                auto_gears_placed += gear.placed
            teleop_gears_placed = 0
            for gear in tmd.teleop_gears:
                teleop_gears_placed += gear.placed

            if auto_gears_placed == 3:
                tmd.auto_points += 120  # rotor 1, 2 in auto
                if teleop_gears_placed == 9:
                    tmd.teleop_points += 80  # rotor 3, 4 in teleop
                elif teleop_gears_placed > 3:
                    tmd.teleop_points += 40  # rotor 4 in teleop
            elif auto_gears_placed > 1:
                tmd.auto_points += 60  # rotor 1 in auto
                if auto_gears_placed + teleop_gears_placed == 12:
                    tmd.teleop_points += 120  # rotor 2, 3, 4 in teleop
                elif auto_gears_placed + teleop_gears_placed > 6:
                    tmd.teleop_points += 80  # rotor 2, 3 in teleop
                elif auto_gears_placed + teleop_gears_placed > 2:
                    tmd.teleop_points += 40  # rotor 2 in teleop
            else:
                # No rotors in auto
                if teleop_gears_placed == 12:
                    tmd.teleop_points += 160  # rotor 1, 2, 3, 4 in teleop
                elif teleop_gears_placed > 6:
                    tmd.teleop_points += 120  # rotor 1, 2, 3 in teleop
                elif teleop_gears_placed > 2:
                    tmd.teleop_points += 80  # rotor 1, 2 in teleop
                else:
                    tmd.teleop_points += 40  # assuming free gear can be placed on rotor 1

            tmd.endgame_points = 50 if tmd.endgame_climb == "successful" else 0

            for key, value in iter(tmd.__dict__.items()):
                if key == 'team_number':
                    continue

                # Convert firebase booleans
                if value == 'true':
                    value = True
                elif value == 'false':
                    value = False

                # strings don't have low level calculations
                if(isinstance(value, int) or
                   isinstance(value, bool) or
                   isinstance(value, float)):

                    # Apply correction down below
                    if key in ["auto_high_goal_correction", "auto_low_goal_correction",
                               "teleop_high_goal_correction", "teleop_low_goal_correction",
                               "auto_points", "teleop_points", "total_points"]:
                        continue

                    # create lists for low level stats calculations
                    if key is not list_dict[tmd.team_number]:
                        list_dict[tmd.team_number][key] = []
                    list_dict[tmd.team_number][key].append(value)
                elif isinstance(value, list):
                    if len(value) > 0:
                        if(isinstance(value[0], Gear)):
                            d = {}
                            for attempt in ['placed', 'dropped']:
                                d[attempt] = {}
                                for location in constants.GEAR_LOCATIONS_WITH_TOTAL:
                                    d[attempt][location] = 0
                            for v in value:
                                attempt = 'placed' if v.placed else 'dropped'
                                d[attempt]['total'] += 1
                                d[attempt][v.location] += 1

                            for period in ['auto', 'teleop']:
                                if period in key:
                                    if "{0:s}_total_gears_placed".format(period) is not list_dict[tmd.team_number]:
                                        for attempt in ['placed', 'dropped']:
                                            for location in constants.GEAR_LOCATIONS_WITH_TOTAL:
                                                list_dict[tmd.team_number]['{0:s}_{1:s}_gears_{2:s}'
                                                                           .format(period, location, attempt)] = []
                                    for attempt in ['placed', 'dropped']:
                                            for location in constants.GEAR_LOCATIONS_WITH_TOTAL:
                                                list_dict[tmd.team_number]['{0:s}_{1:s}_gears_{2:s}'
                                                                           .format(
                                                                               period, location,
                                                                               attempt)].append(d[attempt][location])
                                    break
                elif key == constants.ENDGAME_CLIMB:
                    list_dict[tmd.team_number][constants.ENDGAME_CLIMB_OPTIONS[tmd.endgame_climb]] += 1
                elif key == constants.ENDGAME_CLIMB_TIME:
                    if tmd.endgame_climb_time != constants.ENDGAME_CLIMB_TIME_N_A:
                        match = re.search(pattern, tmd.endgame_climb_time)
                        if match:
                            if constants.ENDGAME_CLIMB_TIME is not list_dict[tmd.team_number]:
                                list_dict[tmd.team_number][constants.ENDGAME_CLIMB_TIME] = []
                            list_dict[tmd.team_number][constants.ENDGAME_CLIMB_TIME].append(int(match.group(0)))

            # Apply correction for high/low goal
            list_dict[tmd.team_number]["auto_high_goal_made"][-1] += tmd.auto_high_goal_correction
            list_dict[tmd.team_number]["auto_low_goal_made"][-1] += tmd.auto_low_goal_correction
            list_dict[tmd.team_number]["teleop_high_goal_made"][-1] += tmd.teleop_high_goal_correction
            list_dict[tmd.team_number]["teleop_low_goal_made"][-1] += tmd.teleop_low_goal_correction

            tmd.auto_points += (int(list_dict[tmd.team_number]["auto_high_goal_made"][-1]) +
                                int(list_dict[tmd.team_number]["auto_low_goal_made"][-1] / 3))
            tmd.teleop_points += (int(list_dict[tmd.team_number]["teleop_high_goal_made"][-1] / 3) +
                                  int(list_dict[tmd.team_number]["teleop_low_goal_made"][-1] / 9))
            tmd.total_points = tmd.auto_points + tmd.teleop_points + tmd.endgame_points

            if "auto_points" in list_dict[tmd.team_number]:
                list_dict[tmd.team_number]["auto_points"] = []
            list_dict[tmd.team_number]["auto_points"].append(tmd.auto_points)
            if "teleop_points" in list_dict[tmd.team_number]:
                list_dict[tmd.team_number]["teleop_points"] = []
            list_dict[tmd.team_number]["teleop_points"].append(tmd.teleop_points)
            if "total_points" in list_dict[tmd.team_number]:
                list_dict[tmd.team_number]["total_points"] = []
            list_dict[tmd.team_number]["total_points"].append(tmd.total_points)
            firebase.update_team_match_data(tmd)

        # Create LowLevelStats
        for team_number, lists in iter(list_dict.items()):
            tcd = TeamCalculatedData()
            tcd.team_number = team_number
            for key, l in iter(lists.items()):
                if key in tcd.__dict__ and isinstance(tcd.__dict__[key], LowLevelStats):
                    tcd.__dict__[key] = LowLevelStats().from_list(l)
            firebase.update_team_calculated_data(tcd)
            logger.info("Updated Low Level Calculations for Team {0:d}".format(team_number))
        # high level calculations

    @staticmethod
    def make_super_calculations(firebase):
        '''Makes all the calculations from the :class:`SuperMatchData`'''

        lists = {}
        for key in TeamCalculatedData().__dict__.keys():
            if 'zscore' in key:
                lists[key[6:]] = {}

        pilot_rating_dict = {}

        # get match rankings from super match data and put in lists for averaging
        for smd in firebase.get_all_super_match_data():
            for key, value in smd.__dict__.items():

                # Create lists for LowLevelStats calculations for pilot rating
                if "pilot_rating" in key:
                    match = firebase.get_match(smd.match_number)
                    if 'blue' in key:
                        team_number = match.teams[int(key[5]) - 1]
                    else:
                        team_number = match.teams[int(key[5]) + 2]
                    if team_number not in pilot_rating_dict:
                        pilot_rating_dict[team_number] = []
                    pilot_rating_dict[team_number].append(int(value[0]))

                    continue

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

        # calculate pilot ratings
        for key, value in pilot_rating_dict.items():
            tcd = firebase.get_team_calculated_data(key)
            tcd.pilot_rating = LowLevelStats().from_list(value)
            firebase.update_team_calculated_data(tcd)

        # calculate zscore for qualitative metrics
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
                firebase_team = firebase.get_team_calculated_data(team['team_number'])
                firebase_team.__dict__["zscore_"+key] = team['zscore']
                firebase_team.__dict__["rank_"+key] = i + 1
                firebase.update_team_calculated_data(firebase_team)

    @staticmethod
    def make_ranking_calculations(firebase, tba):
        '''Pulls the current rankings from `The Blue Alliance <thebluealliance.com>`_
           and predicts the final rankings
        '''
        # Current Rankings
        event_rankings = tba.get_event_rankings()
        Aggregator.set_rankings(event_rankings)
        logger.info("Updated current rankings on Firebase")

        # Predicted Rankings
        teams = []
        for team in firebase.get_teams():
            team.predicted_ranking.played = len(team.info.match_numbers)

            team.predicted_ranking.RPs = team.current_ranking.RPs
            team.predicted_ranking.wins = team.current_ranking.wins
            team.predicted_ranking.ties = team.current_ranking.ties
            team.predicted_ranking.loses = team.current_ranking.loses
            team.predicted_ranking.first_tie_breaker = team.current_ranking.first_tie_breaker
            team.predicted_ranking.second_tie_breaker = team.current_ranking.second_tie_breaker

            for index in range(len(team.completed_matches), len(team.info.match_numbers)):
                match = firebase.get_match(team.info.match_numbers[index])

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
            firebase.update_predicted_team_ranking_data(team.predicted_ranking)
            logger.info("Updated predicted ranking for {0:d} on Firebase".format(team.team_number))

    @staticmethod
    def make_pick_list_calculations(firebase):
        '''Make calculations for :class:`TeamPickAbility` based on :class:`TeamMatchData`,
        :class:`SuperMatchData`, and :class:`TeamCalculatedData`
        '''
        for team in firebase.get_teams().values():
            tc = TeamCalculator(team)

            # First Pick
            team.first_pick.pick_ability = tc.first_pick_ability()
            team.robot_picture_filepath = team.pit.robot_picture_filepath
            team.first_pick.yellow_card = team.calc.yellow_card.total > 0
            team.first_pick.red_card = team.calc.red_card.total > 0
            team.stopped_moving = team.calc.stopped_moving.total > 1
            team.first_pick.top_line = ("PA: {0:f} High Goal: Auto{}, Teleop {}"
                                        .format(team.first_pick.pick_ability,
                                                team.calc.auto_high_goal_made.average,
                                                team.calc.teleop_high_goal_made.average))
            team.first_pick.second_line = ("Average Gears: Auto {}, Teleop {}"
                                           .format(team.calc.auto_total_gears_placed.average,
                                                   team.calc.teleop_total_gears_placed.average))
            team.first_pick.third_line = ("Climb: Percentage {}%, Time {}s"
                                          .format(team.calc.endgame_climb_successful.average,
                                                  team.calc.endgame_climb_time.average))
            firebase.update_first_team_pick_ability(team.first_pick)
            logger.info("Updated first pick info for {0:d} on Firebase".format(team.team_number))

            # Second Pick
            team.second_pick.pick_ability = tc.second_pick_ability()
            team.robot_picture_filepath = team.pit.robot_picture_filepath
            team.second_pick.yellow_card = team.calc.yellow_card.total > 0
            team.second_pick.red_card = team.calc.red_card.total > 0
            team.stopped_moving = team.calc.stopped_moving.total > 1
            team.first_pick.top_line = ("PA: {0:f} Def: {} Con: {} Speed: {}"
                                        .format(team.second_pick.pick_ability,
                                                team.calc.rank_defense,
                                                team.calc.rank_control,
                                                team.calc.rank_speed))
            team.first_pick.second_line = ("Average Gears: Auto {}, Teleop {}"
                                           .format(team.calc.auto_total_gears_placed.average,
                                                   team.calc.teleop_total_gears_placed.average))
            team.first_pick.third_line = ("Climb: Percentage {}%, Time {}s"
                                          .format(team.calc.endgame_climb_successful.average,
                                                  team.calc.endgame_climb_time.average))
            firebase.update_second_team_pick_ability(team.second_pick)
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
            firebase.update_third_team_pick_ability(team.third_pick)
            logger.info("Updated third pick info for {0:d} on Firebase".format(team.team_number))
