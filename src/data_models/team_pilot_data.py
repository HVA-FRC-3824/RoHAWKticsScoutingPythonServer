from .data_model import DataModel
from .low_level_stats import LowLevelStats


class TeamPilotData(DataModel):
    '''All the calculated pilot data for a team'''
    def __init__(self, d=None):
        DataModel.__init__(self)
        self.team_number = -1
        self.rating = LowLevelStats()
        self.lifts = LowLevelStats()
        self.drops = LowLevelStats()

        if d is not None:
            self.set(d)

    @staticmethod
    def from_list(mtpds):
        rv = TeamPilotData()

        if len(mtpds) > 0:
            rv.team_number = mtpds[0].team_number

        rating_list = []
        lifts_list = []
        drops_list = []

        for mtpd in mtpds:
            rating = int(mtpd.rating[0])
            if rating != 0:
                rating_list.append(rating)
            lifts_list.append(mtpd.lifts)
            drops_list.append(mtpd.drops)

        rv.rating = LowLevelStats.from_list(rating_list)
        rv.lifts = LowLevelStats.from_list(lifts_list)
        rv.drops = LowLevelStats.from_list(drops_list)

        return rv
