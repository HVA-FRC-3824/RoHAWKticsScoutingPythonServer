from .data_model import DataModel
from .low_level_stats import LowLevelStats


class GearLocationResults(DataModel):
    def __init__(self, d=None):
        DataModel.__init__(self)

        self.placed = LowLevelStats()
        self.dropped = LowLevelStats()

        if d is not None:
            self.set(d)

    @staticmethod
    def from_list(list_):
        rv = GearLocationResults()

        placed_list = []
        dropped_list = []

        for gear in list_:
            placed_list.append(gear[0])
            dropped_list.append(gear[1])

        rv.placed = LowLevelStats.from_list(placed_list)
        rv.dropped = LowLevelStats.from_list(dropped_list)

        return rv
