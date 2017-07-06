from .data_model import DataModel


class Gear(DataModel):
    def __init__(self, d=None):
        self.location = ""
        self.placed = False
        self.dropped = False
        if d is not None:
            self.set(d)

    @classmethod
    def get_csv_field_names(cls) -> list:
        return ['total_placed', 'total_dropped', 'far_placed', 'far_dropped', 'center_placed', 'center_dropped', 'near_placed', 'near_dropped', 'loading_station_dropped']

    def to_csv_row(self) -> dict:
        d = {}
        if self.location == 'far':
            if self.placed:
                d['total_placed'] = 1
                d['far_placed'] = 1
            else:
                d['total_dropped'] = 1
                d['far_dropped'] = 1
        elif self.location == 'center':
            if self.placed:
                d['total_placed'] = 1
                d['center_placed'] = 1
            else:
                d['total_dropped'] = 1
                d['center_dropped'] = 1
        elif self.location == 'near':
            if self.placed:
                d['total_placed'] = 1
                d['near_placed'] = 1
            else:
                d['total_dropped'] = 1
                d['near_dropped'] = 1
        elif self.location == 'loading station':
            d['total_dropped'] = 1
            d['loading_station_dropped'] = 1
        return d
