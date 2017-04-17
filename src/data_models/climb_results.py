from .data_model import DataModel
from .low_level_stats import LowLevelStats
import re
import logging

from ourlogging import setup_logging
setup_logging(__file__)
logger = logging.getLogger(__name__)


class ClimbResults(DataModel):
    def __init__(self, d=None):
        DataModel.__init__(self)

        self.success = 0
        self.fell = 0
        self.failed = 0
        self.no_attempt = 0
        self.foul_credit = 0
        self.total = 0

        self.success_percentage = 0

        self.time = LowLevelStats()

        if d is not None:
            self.set(d)

    @staticmethod
    def from_lists(results, times):
        rv = ClimbResults()

        rv.total = len(results)

        time_list = []
        pattern = re.compile(r"< (\d+)s")

        for i in range(rv.total):
            if results[i] == "Successful":
                rv.success += 1
                match = re.search(pattern, times[i])
                if match:
                    time_list.append(int(match.group(1)))
                else:
                    logger.error("Successful climb, but no time")
            elif results[i] == "Robot fell":
                rv.fell += 1
            elif results[i] == "Did not finish in time":
                rv.failed += 1
            elif results[i] == "Credited through foul":
                rv.foul_credit += 1
            elif results[i] == "No attempt":
                rv.no_attempt += 1
            else:
                logger.error("Unknown climb result")

        rv.time = LowLevelStats.from_list(time_list)

        rv.success_percentage = rv.success / rv.total

        return rv
