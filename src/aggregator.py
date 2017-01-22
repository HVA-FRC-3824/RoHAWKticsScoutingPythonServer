import logging
import re

from ourlogging import setup_logging

setup_logging(__file__)
logger = logging.getLogger(__name__)

class Aggregator:
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
            tmd.teleop_points = 0
            tmd.endgame_points = 50 if tmd.endgame_climb == "successful" else 0
            tmd.total_points = tmd.auto_points + tmd.teleop_points + tmd.endgame_points

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
                                                list_dict[tmd.team_number]['{0:s}_{1:s}_gears_{2:s}'.format(period, location,attempt)] = []
                                    for attempt in ['placed', 'dropped']:
                                            for location in constants.GEAR_LOCATIONS_WITH_TOTAL:
                                                list_dict[tmd.team_number]['{0:s}_{1:s}_gears_{2:s}'.format(period, location,attempt)].append(d[attempt][location])
                                    break
                elif key == constants.ENDGAME_CLIMB:
                    list_dict[tmd.team_number][constants.ENDGAME_CLIMB_OPTIONS[tmd.endgame_climb]] += 1
                elif key == constants.ENDGAME_CLIMB_TIME:
                    if tmd.endgame_climb_time != constants.ENDGAME_CLIMB_TIME_N_A:
                        match = re.search(pattern, tmd.endgame_climb_time)
                        if match:
                            if constants.ENDGAME_CLIMB_TIME is not list_dict[tmd.team_number]:
                                list_dict[tmd.team_number][constants.ENDGAME_CLIMB_TIME] = []
                            list_dict[tmd.team_number][constants.ENDGAME_CLIMB_TIME].append(int(m.group(0)))

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

    @staticmethod
    def make_super_calculations(firebase):
        '''Makes all the calculations from the :class:`SuperMatchData`'''
        lists = {}
        for key in TeamCalculatedData().__dict__.keys():
            if 'zscore' in key:
                lists[key[6:]] = {}

        # get match rankings from super match data and put in lists for averaging
        for smd in firebase.get_all_super_match_data():
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


    @staticmethod
    def make_ranking_calculations(firebase, tba):
        '''Pulls the current rankings from `The Blue Alliance <thebluealliance.com>`_
           and predicts the final rankings
        '''
        # Current Rankings
        event_rankings = tba.get_event_rankings()
        self.set_rankings(event_rankings)
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
