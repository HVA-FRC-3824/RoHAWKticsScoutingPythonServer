import logging
import re
import scipy.stats as stats

from constants import Constants

from data_models.gear import Gear
from data_models.match import Match
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
        num_matches = -1
        event_matches.sort(key=lambda team: int(team['match_number']))
        for tba_match in event_matches:
            if tba_match['comp_level'] != "qm":
                continue

            if tba_match['match_number'] > num_matches:
                num_matches = tba_match['match_number']

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
        return team_matches, num_matches

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
        team_numbers = []
        event_teams.sort(key=lambda team: int(team['team_number']))
        for tba_team in event_teams:
            info = TeamLogistics()
            info.team_number = tba_team['team_number']
            info.nickname = tba_team['nickname']
            info.match_numbers = team_matches[info.team_number]
            team_logistics.append(info)

            team_numbers.append(info.team_number)

            pit = TeamPitData()
            pit.team_number = info.team_number
            firebase.update_team_pit_data(pit)

            pick = TeamPickAbility()
            pick.team_number = info.team_number
            pick.nickname = info.nickname
            firebase.update_team_first_pick_ability(pick)
            firebase.update_team_second_pick_ability(pick)
            firebase.update_team_third_pick_ability(pick)
            logger.info("Team {0:d} added".format(info.team_number))

        min_matches = 100  # Each team should always have less than 100 matches
        for team in team_logistics:
            if len(team.match_numbers) < min_matches:
                min_matches = len(team_matches)

        for team in team_logistics:
            if len(team.match_numbers) > min_matches:
                team.surrogate_match_number = team.matches[3]
            firebase.update_team_logistics(team)

        return team_numbers

    @staticmethod
    def set_rankings(firebase, event_rankings):
        '''Convert the ranking information from `The Blue Alliance <thebluealliance.com>`_
           to the :class:`TeamRankingData`
        '''
        first = True

        for tba_ranking in event_rankings:
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
            ranking.first_tie_breaker = int(float(tba_ranking_list[3]))
            ranking.second_tie_breaker = int(float(tba_ranking_list[4]))
            ranking.played = int(tba_ranking_list[8])
            print(ranking)
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
            logger.info("Match Calculating: Team Number: {0:d}, Match Number: {1:d}".format(tmd.team_number, tmd.match_number))
            if tmd.team_number not in list_dict:
                list_dict[tmd.team_number] = {}

            # calculate the points score by this particular team in this match (as if they were by
            # themselves). fuel points will be added later after corrections have been added
            tmd.auto_points = 0
            tmd.auto_points += 5 if tmd.auto_baseline else 0
            tmd.teleop_points = 0

            auto_gears_placed = 0
            for gear in tmd.auto_gears:
                auto_gears_placed += gear.placed
            teleop_gears_placed = 0
            for gear in tmd.teleop_gears:
                teleop_gears_placed += gear.placed
            rotor = 0
            if auto_gears_placed == 3:
                tmd.auto_points += 120  # rotor 1, 2 in auto
                rotor = 2
            elif auto_gears_placed > 1:
                tmd.auto_points += 60  # rotor 1 in auto
                rotor = 1

            if auto_gears_placed + teleop_gears_placed >= 12:
                tmd.teleop_points += (4 - rotor) * 40
            elif auto_gears_placed + teleop_gears_placed >= 6:
                tmd.teleop_points += (3 - rotor) * 40
            elif auto_gears_placed + teleop_gears_placed >= 2:
                tmd.teleop_points += (2 - rotor) * 40
            else:
                tmd.teleop_points += 40  # assuming free gear can be placed on rotor 1

            tmd.endgame_points = 50 if tmd.endgame_climb == "successful" else 0

            for key, value in iter(tmd.__dict__.items()):
                if key == 'team_number':
                    continue

                # Convert firebase booleans (not sure if needed)
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
                    if key not in list_dict[tmd.team_number]:
                        list_dict[tmd.team_number][key] = []
                    list_dict[tmd.team_number][key].append(value)
                # The only lists in this data model are the auto_gears and teleop_gears
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
                # Break up the climb text into lists for LowLevelStats
                elif key == constants.ENDGAME_CLIMB_KEY:
                    for key, option in constants.ENDGAME_CLIMB_OPTIONS.items():
                        if(option not in list_dict[tmd.team_number]):
                            list_dict[tmd.team_number][option] = []
                        if tmd.endgame_climb == key:
                            list_dict[tmd.team_number][option].append(1)
                        else:
                            list_dict[tmd.team_number][option].append(0)

                elif key == constants.ENDGAME_CLIMB_TIME_KEY:
                    # Only track time on climbs that were successful
                    if(tmd.endgame_climb_time != constants.ENDGAME_CLIMB_TIME_N_A and
                       tmd.endgame_climb == constants.ENDGAME_CLIMB_SUCCESSFUL):
                        match = re.search(pattern, tmd.endgame_climb_time)
                        if match:
                            if constants.ENDGAME_CLIMB_TIME_KEY not in list_dict[tmd.team_number]:
                                list_dict[tmd.team_number][constants.ENDGAME_CLIMB_TIME_KEY] = []
                            list_dict[tmd.team_number][constants.ENDGAME_CLIMB_TIME_KEY].append(int(match.group(1)))

            # Apply correction for high/low goal
            list_dict[tmd.team_number]["auto_high_goal_made"][-1] += tmd.auto_high_goal_correction
            list_dict[tmd.team_number]["auto_low_goal_made"][-1] += tmd.auto_low_goal_correction
            list_dict[tmd.team_number]["teleop_high_goal_made"][-1] += tmd.teleop_high_goal_correction
            list_dict[tmd.team_number]["teleop_low_goal_made"][-1] += tmd.teleop_low_goal_correction

            # points updated with fuel points that have been corrected
            tmd.auto_points += (int(list_dict[tmd.team_number]["auto_high_goal_made"][-1]) +
                                int(list_dict[tmd.team_number]["auto_low_goal_made"][-1] / 3))
            tmd.teleop_points += (int(list_dict[tmd.team_number]["teleop_high_goal_made"][-1] / 3) +
                                  int(list_dict[tmd.team_number]["teleop_low_goal_made"][-1] / 9))
            tmd.total_points = tmd.auto_points + tmd.teleop_points + tmd.endgame_points

            if "auto_points" not in list_dict[tmd.team_number]:
                list_dict[tmd.team_number]["auto_points"] = []
            list_dict[tmd.team_number]["auto_points"].append(tmd.auto_points)
            if "teleop_points" not in list_dict[tmd.team_number]:
                list_dict[tmd.team_number]["teleop_points"] = []
            list_dict[tmd.team_number]["teleop_points"].append(tmd.teleop_points)
            if "total_points" not in list_dict[tmd.team_number]:
                list_dict[tmd.team_number]["total_points"] = []
            list_dict[tmd.team_number]["total_points"].append(tmd.total_points)
            firebase.update_team_match_data(tmd)

        logger.info("Creating Low Level Statistics")

        # Create LowLevelStats
        for team_number, lists in iter(list_dict.items()):
            tcd = TeamCalculatedData()
            tcd.team_number = team_number
            for key, l in lists.items():
                if key in tcd.__dict__ and isinstance(tcd.__dict__[key], LowLevelStats):
                    tcd.__dict__[key] = LowLevelStats().from_list(l)
            firebase.update_team_calculated_data(tcd)
            logger.info("Updated Low Level Calculations for Team {0:d}".format(team_number))

    @staticmethod
    def make_super_calculations(firebase):
        '''Makes all the calculations from the :class:`SuperMatchData`'''

        lists = {}
        for key in TeamCalculatedData().__dict__.keys():
            if 'zscore' in key:
                lists[key[6:]] = {}

        print(lists)

        pilot_rating_dict = {}

        # get match rankings from super match data and put in lists for averaging
        for match_number, smd in firebase.get_all_super_match_data().items():
            logger.info("calculations for super match {0:d}".format(match_number))
            for key, value in smd.__dict__.items():

                # Create lists for LowLevelStats calculations for pilot rating
                if "pilot_rating" in key:
                    match = firebase.get_match(smd.match_number)
                    if 'blue' in key:
                        team_number = match.teams[int(key[4]) - 1]
                    else:
                        team_number = match.teams[int(key[3]) + 2]
                    if team_number not in pilot_rating_dict:
                        pilot_rating_dict[team_number] = []
                    # first character of the options is a number
                    # Don't include when this pilot isn't used
                    if int(value[0]) == 0:
                        continue
                    pilot_rating_dict[team_number].append(int(value[0]))

                    continue

                # get the keys of the qualitative input
                if 'blue' in key:
                    key = key[4:]
                # handle both blue and red on the blue
                elif 'red' in key:
                    continue

                # key is in the list if it is a qualitative unput
                if key in lists:
                    match = firebase.get_match(smd.match_number)
                    for i, team_number in enumerate(match.teams):
                        if team_number not in lists[key]:
                            lists[key][team_number] = []

                        # first 3 team numbers are blue. second 3 team numbers are red
                        if i < 3:
                            match_rank = 4 - smd.__dict__["blue" + key][i]
                        else:
                            match_rank = 4 - smd.__dict__["red" + key][i - 3]
                        if match_rank == 3:
                            match_rank = 4
                        lists[key][team_number].append(match_rank)

        logger.info("Making pilot rating calculations")

        # calculate pilot ratings
        for key, value in pilot_rating_dict.items():
            tcd = firebase.get_team_calculated_data(key)
            tcd.pilot_rating = LowLevelStats().from_list(value)
            firebase.update_team_calculated_data(tcd)

        logger.info("Making zscore calculations")

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
                zscore_components[key]['team_numbers'].append(team_number)
                zscore_components[key]['averages'].append(average / len(list[key][team_number]))
            zscore_components[key]['zscores'] = stats.zscore(zscore_components[key]['averages'])

            # Create list for sorting
            teams = []
            for i in range(len(zscore_components[key]['team_numbers'])):
                team = {}
                team['team_number'] = zscore_components[key]['team_numbers'][i]
                team['zscore'] = zscore_components[key]['zscores'][i]
            # Make the zscore negative for sorting so larger numbers are at the beginning
            teams = sorted(teams, key=lambda team: -team['zscore'])

            # add calculations to firebase
            for i, team in enumerate(teams):
                firebase_team = firebase.get_team_calculated_data(team['team_number'])
                firebase_team.__dict__["zscore"+key] = team['zscore']
                firebase_team.__dict__["rank"+key] = i + 1
                firebase.update_team_calculated_data(firebase_team)

    @staticmethod
    def make_ranking_calculations(firebase, tba):
        '''Pulls the current rankings from `The Blue Alliance <thebluealliance.com>`_
           and predicts the final rankings
        '''
        logger.info("Pulling current rankings")
        # Current Rankings
        event_rankings = tba.get_event_rankings()
        Aggregator.set_rankings(firebase, event_rankings)
        logger.info("Updated current rankings on Firebase")

        logger.info("Predicting final rankings")
        # Predicted Rankings
        teams = []
        for team_number, team in firebase.get_teams().items():
            team.predicted_ranking = TeamRankingData({'team_number': team.team_number})
            team.predicted_ranking.played = len(team.info.match_numbers)

            if(team.current_ranking is None):
                team.current_ranking = TeamRankingData({'team_number': team.team_number})

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
                    ac = AllianceCalculator(match.teams[0:2])
                    opp = AllianceCalculator(match.teams[3:5])
                else:
                    ac = AllianceCalculator(match.teams[3:5])
                    opp = AllianceCalculator(match.teams[0:2])

                if ac.win_probability_over(opp) > 0.5:
                    team.predicted_ranking.wins += 1
                    team.predicted_ranking.RPs += 2
                elif opp.win_probabiliy_over(ac) > 0.5:
                    team.predicted_ranking.loses += 1
                else:
                    team.predicted_ranking.ties += 1
                    team.predicted_ranking.RPs += 1

                team.predicted_ranking.RPs += 1 if ac.rotor_chance() > 0.5 else 0
                team.predicted_ranking.RPs += 1 if ac.pressure_chance() > 0.5 else 0

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
        for team_number, team in firebase.get_teams().items():
            tc = TeamCalculator(team)

            # First Pick
            team.first_pick.pick_ability = tc.first_pick_ability()
            if(team.pit.robot_image_default > -1):
                team.first_pick.robot_picture_filepath = team.pit.robot_image_filepaths[team.pit.robot_image_default]
            team.first_pick.yellow_card = team.calc.yellow_card.total > 0
            team.first_pick.red_card = team.calc.red_card.total > 0
            team.first_pick.stopped_moving = team.calc.stopped_moving.total > 1
            team.first_pick.top_line = ("PA: {0:0.2f} High Goal: Auto{1:0.2f}, Teleop {2:0.2f}"
                                        .format(team.first_pick.pick_ability,
                                                team.calc.auto_high_goal_made.average,
                                                team.calc.teleop_high_goal_made.average))
            team.first_pick.second_line = ("Average Gears: Auto {0:0.2f}, Teleop {1:0.2f}"
                                           .format(team.calc.auto_total_gears_placed.average,
                                                   team.calc.teleop_total_gears_placed.average))
            team.first_pick.third_line = ("Climb: Percentage {0:0.2f}%, Time {1:0.2f}s"
                                          .format(team.calc.endgame_climb_successful.average * 100,
                                                  team.calc.endgame_climb_time.average))
            team.first_pick.fourth_line = ""
            firebase.update_team_first_pick_ability(team.first_pick)
            logger.info("Updated first pick info for {0:d} on Firebase".format(team.team_number))

            # Second Pick
            team.second_pick.pick_ability = tc.second_pick_ability()
            if(team.pit.robot_image_default > -1):
                team.second_pick.robot_picture_filepath = team.pit.robot_image_filepaths[team.pit.robot_image_default]
            team.second_pick.yellow_card = team.calc.yellow_card.total > 0
            team.second_pick.red_card = team.calc.red_card.total > 0
            team.second_pick.stopped_moving = team.calc.stopped_moving.total > 1
            team.second_pick.top_line = ("PA: {0:0.2f} Defense: {1:d} Control: {2:d} Speed: {3:d} Torque: {3:d}"
                                         .format(team.second_pick.pick_ability,
                                                 team.calc.rank_defense,
                                                 team.calc.rank_control,
                                                 team.calc.rank_speed,
                                                 team.calc.rank_torque))
            team.second_pick.second_line = ("Average Gears: Auto {0:0.2f}, Teleop {1:0.2f}"
                                            .format(team.calc.auto_total_gears_placed.average,
                                                    team.calc.teleop_total_gears_placed.average))
            team.second_pick.third_line = ("Climb: Percentage {0:0.2f}%, Time {1:0.2f}s"
                                           .format(team.calc.endgame_climb_successful.average * 100,
                                                   team.calc.endgame_climb_time.average))
            team.second_pick.fourth_line = ("Weight: {0:0.2f} lbs, PL: {1:s}"
                                            .format(team.pit.weight, team.pit.programming_language))
            firebase.update_team_second_pick_ability(team.second_pick)
            logger.info("Updated second pick info for {0:d} on Firebase".format(team.team_number))

            # Third Pick
            '''
            team.third_pick.pick_ability = tc.third_pick_ability()
            team.third_pick.robot_picture_filepath = team.pit.robot_image_filepaths[team.pit.robot_image_default]
            team.third_pick.yellow_card = team.calc.yellow_card.total > 0
            team.third_pick.red_card = team.calc.red_card.total > 0
            team.third_pick.stopped_moving = team.calc.stopped_moving.total > 1
            team.third_pick.top_line = "PA: {0:f}".format(team.third_pick.pick_ability)
            team.third_pick.second_line = "".format()
            team.third_pick.third_line = "".format()
            team.third_pick.fourth_line = ""
            firebase.update_team_third_pick_ability(team.third_pick)
            logger.info("Updated third pick info for {0:d} on Firebase".format(team.team_number))
            '''
