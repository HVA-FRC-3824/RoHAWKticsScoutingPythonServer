from .data_model import DataModel
from .low_level_stats import LowLevelStats


class GoalResults(DataModel):
    def __init__(self, d=None):
        DataModel.__init__(self)

        self.made = LowLevelStats()
        self.missed = LowLevelStats()

        if d is not None:
            self.set(d)

    @staticmethod
    def from_lists(made_list, missed_list):
        rv = GoalResults()

        rv.made = LowLevelStats.from_list(made_list)
        rv.missed = LowLevelStats.from_list(missed_list)

        return rv
