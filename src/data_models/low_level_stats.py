import math
from .data_model import DataModel


class LowLevelStats(DataModel):
    '''Data Model that holds low level statistics (average, min, max, total, standard deviation)

    Note:
        This should not be created directly and instead made using :func:`from_list`
    '''
    def __init__(self, d=None):
        self.max = 0
        self.min = 0
        self.average = 0
        self.std = 0
        self.total = 0

        if d is not None:
            self.set(d)

    @staticmethod
    def from_list(list_):
        '''Create the :class:`LowLevelStats` from a list of data points

        Args:
            list_ (`list`): a list of int, float, or bool that is used to aggregate
            the low level statistics
        '''
        if len(list_) == 0:
            return

        if isinstance(list_[0], bool):
            return LowLevelStats.from_boolean(list_)
        elif isinstance(list_[0], int):
            return LowLevelStats.from_int(list_)
        elif isinstance(list_[0], float):
            return LowLevelStats.from_float(list_)
        else:
            raise Exception("Unknown type")

    @staticmethod
    def from_boolean(list_):
        '''Creates a :class:`LowLevelStats` from a list of bools'''
        l = LowLevelStats()
        l.max = 0.0
        l.min = 1.0

        for item in list_:
            if item:
                l.max = 1.0
                l.total += 1.0
            else:
                l.min = 0.0

        l.average = l.total / len(list_)

        for item in list_:
            if item:
                l.std += (1.0 - l.average) ** 2
            else:
                l.std += l.average ** 2
        l.std /= len(list_)
        l.std = math.sqrt(l.std)
        return l

    @staticmethod
    def from_int(list_):
        '''Creates a :class:`LowLevelStats` from a list of ints'''
        l = LowLevelStats()
        l.max = -float("inf")
        l.min = float("inf")

        for item in list_:
            if item > l.max:
                l.max = item

            if item < l.min:
                l.min = item

            l.total += item

        l.average = l.total / len(list_)

        for item in list_:
            l.std += (item - l.average) ** 2
        l.std /= len(list_)
        l.std = math.sqrt(l.std)
        return l

    @staticmethod
    def from_float(list_):
        '''Creates a :class:`LowLevelStats` from a list of floats'''
        l = LowLevelStats()
        l.max = -float("inf")
        l.min = float("inf")

        for item in list_:
            if item > l.max:
                l.max = item

            if item < l.min:
                l.min = item

            l.total += item

        l.average = l.total / len(list_)

        for item in list_:
            l.std += (item - l.average) ** 2
        l.std /= len(list_)
        l.std = math.sqrt(l.std)
        return l
