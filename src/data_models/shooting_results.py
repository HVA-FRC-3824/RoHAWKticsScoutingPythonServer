from .data_model import DataModel
from .goal_results import GoalResults


class ShootingResults(DataModel):
    def __init__(self, d=None):
        DataModel.__init__(self)

        self.high = GoalResults()
        self.low = GoalResults()

        if d is not None:
            self.set(d)

    @staticmethod
    def from_lists(high_made, high_missed, low_made, low_missed):
        rv = ShootingResults()

        rv.high = GoalResults.from_lists(high_made, high_missed)
        rv.low = GoalResults.from_lists(low_made, low_missed)

        return rv
