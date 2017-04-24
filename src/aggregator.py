import logging
import scipy.stats as stats


from database import Database
from data_models.team_ranking_data import TeamRankingData
from data_models.team_calculated_data import TeamCalculatedData
from data_models.team_qualitative_data import TeamQualitativeData
from data_models.team_pilot_data import TeamPilotData
from data_models.team_pick_ability import TeamPickAbility

from ourlogging import setup_logging

setup_logging(__file__)
logger = logging.getLogger(__name__)


class Aggregator:
    @staticmethod
    def team_calc(team_number):
        logger.info("Updating team {}".format(team_number))
        database = Database()

        logger.info("Updating team calculated data for {}".format(team_number))

        team_info = database.get_team_logistics(team_number)
        if team_info is None:
            return
        tmds = []
        for match_number in team_info.match_numbers:
            tmd = database.get_team_match_data(team_number=team_number, match_number=match_number)
            if tmd is not None:
                tmds.append(tmd)
        tcd = TeamCalculatedData.from_list(tmds)
        database.set_team_calculated_data(tcd)

        logger.info("Updating team pick ability for {}".format(team_number))
        try:
            tpa = TeamPickAbility.calculate_first_pick_ability(team_number, database)
        except:
            pass
        else:
            database.set_team_pick_ability(tpa, Database.FIRST_PICK)
        # tpa = TeamPickAbility.calculate_second_pick_ability(team_number, database)
        # database.set_team_pick_ability(tpa, Database.SECOND_PICK)
        # tpa = TeamPickAbility.calculate_third_pick_ability(team_number, database)
        # database.set_team_pick_ability(tpa, Database.THIRD_PICK)

    @staticmethod
    def match_calc(current_match_number):
        logger.info("Updating match {}".format(current_match_number))
        database = Database()

        match = database.get_match(current_match_number)
        if match is None:
            return
        # update_match_numbers = []

        # Update the team calculated data
        for team_number in match.team_numbers:
            # logger.info("Updating team calculated data for {}".format(team_number))

            Aggregator.team_calc(team_number)
        '''
            team_info = database.get_team_logistics(team_number)
            tmds = []
            for match_number in team_info.match_numbers:
                tmd = database.get_team_match_data(team_number=team_number, match_number=match_number)
                if tmd is not None:
                    tmds.append(tmd)
                # We have hit the current match
                elif match_number not in update_match_numbers:
                    update_match_numbers.append(match_number)
            tcd = TeamCalculatedData.from_list(tmds)
            database.set_team_calculated_data(tcd)

        # update match predictions
        for match_number in update_match_numbers:
            logger.info("Updating match prediction for {}".format(match_number))
            m = database.get_match(match_number)
            m.update_prediction()
            database.set_match(m)

        # update team ranking data
        for team_number in match_number.team_numbers:
            logger.info("Updating team ranking prediction for {}".format(team_number))
            trd = TeamRankingData.update_prediction(team_number)
            database.set_team_ranking_data(trd, database.PREDICTED)

        # update team pick ability
        for team_number in match_number.team_numbers:
            logger.info("Updating team pick ability for {}".format(team_number))
            tpa = TeamPickAbility.calculate_first_pick_ability(team_number, database)
            database.set_team_pick_ability(tpa, Database.FIRST_PICK)
            # tpa = TeamPickAbility.calculate_second_pick_ability(team_number, database)
            # database.set_team_pick_ability(tpa, Database.SECOND_PICK)
            # tpa = TeamPickAbility.calculate_third_pick_ability(team_number)
            # database.set_team_pick_ability(tpa, Database.THIRD_PICK)
        '''

    @staticmethod
    def super_calc():
        logger.info("Updating team qualitative data")
        database = Database()

        lists = {}
        for key in TeamCalculatedData().__dict__.keys():
            if 'zscore' in key:
                lists[key[6:]] = {}

        # get match rankings from super match data and put in lists for averaging
        for match_number, smd in database.get_all_super_match_data().items():
            logger.info("calculations for super match {0:d}".format(match_number))
            for key, value in smd.__dict__.items():

                # get the keys of the qualitative input
                if 'blue' in key:
                    key = key[4:]
                # handle both blue and red on the blue
                elif 'red' in key:
                    continue

                # key is in the list if it is a qualitative input
                if key in lists:
                    for color in ['blue', 'red']:
                        for team_number, rating in smd.__dict__[color + key].items():
                            if rating == 3:
                                rating = 4
                            lists[key][int(team_number)].append(rating)

        logger.info("Making zscore calculations")

        # calculate zscore for qualitative metrics
        team_qualitative = {}
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
                zscore_components[key]['averages'].append(average / len(lists[key][team_number]))
            zscore_components[key]['zscores'] = stats.zscore(zscore_components[key]['averages'])
            # Create list for sorting
            teams = []
            for i in range(len(zscore_components[key]['team_numbers'])):
                team = {}
                team['team_number'] = zscore_components[key]['team_numbers'][i]
                team['zscore'] = zscore_components[key]['zscores'][i]
                teams.append(team)

            # Make the zscore negative for sorting so larger numbers are at the beginning
            teams = sorted(teams, key=lambda team: -team['zscore'])

            for i, team in enumerate(teams):
                team_qualitative[team['team_number']][key[1:]] = {"zscore": team['zscore'], "rank": i + 1}

        # add calculations to firebase
        for team_number in team_qualitative:
            t = TeamQualitativeData(team_qualitative[team_number])
            t.team_number = team_number
            database.set_team_qualitative_data(t)

    @staticmethod
    def pilot_calc(current_match_number):
        logger.info("Updating pilot data for match {}".format(current_match_number))
        database = Database()
        match = database.get_match(current_match_number)

        if match is None:
            return

        for team_number in match.team_numbers:
            Aggregator.team_pilot_calc(team_number)

    @staticmethod
    def team_pilot_calc(team_number):
        database = Database()
        logger.info("Updating pilot data for team {}".format(team_number))
        team_info = database.get_team_logistics(team_number)
        if team_info is None:
            return

        mtpds = []
        for match_number in team_info.match_numbers:
            mpd = database.get_match_pilot_data(match_number)
            if mpd is not None:
                for t in mpd.teams:
                    if t.team_number == team_number:
                        mtpds.append(t)
                        break
        tpd = TeamPilotData.from_list(mtpds)
        database.set_team_pilot_data(tpd)
