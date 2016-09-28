import math
import sys
from .data_model import DataModel


class LowLevelStats(DataModel):
    def __init__(self, list_):
        self.max = 0.0
        self.min = 0.0
        self.average = 0.0
        self.std = 0.0
        self.total = 0.0

        if len(list_) == 0:
            return

        if isinstance(list_[0], bool):
            self.boolean_init(list_)
        elif isinstance(list_[0], int):
            self.int_init(list_)
        elif isinstance(list_[0], float):
            self.float_init(list_)
        else:
            raise Exception("Unknown type")

    def boolean_init(self, list_):
        self.max = 0.0
        self.min = 1.0

        for item in list_:
            if item:
                self.max = 1.0
                self.total += 1.0
            else:
                self.min = 0.0

        self.average = self.total / len(list_)

        for item in list_:
            if item:
                self.std += (1.0 - self.average) ** 2
            else:
                self.std += self.average ** 2
        self.std /= len(list_)
        self.std = math.sqrt(self.std)

    def int_init(self, list_):
        self.max = -float("inf")
        self.min = float("inf")

        for item in list_:
            if item > self.max:
                self.max = item

            if item < self.min:
                self.min = item

            self.total += item

        self.average = self.total / len(list_)

        for item in list_:
            self.std += (item - self.average) ** 2
        self.std /= len(list_)
        self.std = math.sqrt(self.std)

    def float_init(self, list_):
        self.max = sys.floatmin
        self.min = sys.floatmax

        for item in list_:
            if item > self.max:
                self.max = item

            if item < self.min:
                self.min = item

            self.total += item

        self.average = self.total / len(list_)

        for item in list_:
            self.std += (item - self.average) ** 2
        self.std /= len(list_)
        self.std = math.sqrt(self.std)
