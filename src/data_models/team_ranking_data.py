from .data_model import DataModel
from .match import Match


class TeamRankingData(DataModel):
    '''Data about a team's current or predicted ranking'''
    def __init__(self, d=None):
        DataModel.__init__(self)

        self.team_number = -1

        self.rank = 0
        self.RPs = 0
        self.wins = 0
        self.ties = 0
        self.losses = 0
        self.played = 0
        self.first_tie_breaker = 0
        self.second_tie_breaker = 0

        if d is not None:
            self.set(d)

    @staticmethod
    def create_prediction(team_number):
        # Solves cyclical dependency
        from database import Database
        database = Database()

        # Start with current ranking
        predicted = database.get_team_ranking_data(team_number, Database.CURRENT)

        logistics = database.get_team_logistics(team_number)

        completed_matches = predicted.played

        # unaverage RPs
        predicted.RPS *= completed_matches

        # go through yet to be played matches
        for i in range(len(logistics.match_numbers) - completed_matches):
            # ignore surrogate matches
            if logistics.match_numbers[i] == logistics.surrogate_match_number:
                continue

            predicted.played += 1
            match = database.get_match(logistics.match_numbers[i])

            # 2 rp for win, 1 for tie, 0 for loss
            if match.predicted_score[Match.BLUE] > match.predicted_score[Match.RED]:
                if match.is_blue(team_number):
                    predicted.wins += 1
                    predicted.RPs += 2
                else:
                    predicted.losses += 1
            elif match.predicted_score[Match.BLUE] < match.predicted_score[Match.RED]:
                if match.is_red(team_number):
                    predicted.wins += 1
                    predicted.RPs += 2
                else:
                    predicted.losses += 1
            else:
                predicted.ties += 1
                predicted.RPs += 1

            # RP for 40 kpa, 4 rotors
            # First tie breaker is total points
            # Second tie breaker is auto points
            if match.is_blue(team_number):
                predicted.first_tie_breaker += match.predicted_score[Match.BLUE]
                predicted.second_tie_breaker += match.predicted_auto[Match.BLUE]
                if match.predicted_kpa_rp[Match.BLUE]:
                    predicted.RPs += 1
                if match.predicted_rotor_rp[Match.BLUE]:
                    predicted.RPs += 1
            else:
                predicted.first_tie_breaker += match.predicted_score[Match.RED]
                predicted.second_tie_breaker += match.predicted_auto[Match.RED]
                if match.predicted_kpa_rp[Match.RED]:
                    predicted.RPs += 1
                if match.predicted_rotor_rp[Match.RED]:
                    predicted.RPs += 1

        # average RPs
        predicted.RPs /= predicted.played

        return predicted

    @staticmethod
    def from_tba_ranking(tba_ranking):
        ranking = TeamRankingData()
        ranking.team_number = int(tba_ranking.team_key[3:])
        ranking.played = tba_ranking.matches_played
        ranking.wins = tba_ranking.record.wins
        ranking.ties = tba_ranking.record.ties
        ranking.losses = tba_ranking.record.losses
        ranking.RPs = tba_ranking.sort_orders[0]
        ranking.first_tie_breaker = tba_ranking.sort_orders[1]
        ranking.second_tie_breaker = tba_ranking.sort_orders[2]
        return ranking
