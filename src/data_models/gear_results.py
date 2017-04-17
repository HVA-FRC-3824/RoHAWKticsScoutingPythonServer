from .data_model import DataModel
from .gear_location_results import GearLocationResults


class GearResults(DataModel):
    def __init__(self, d=None):
        self.total = GearLocationResults()
        self.near = GearLocationResults()
        self.center = GearLocationResults()
        self.far = GearLocationResults()

        if d is not None:
            self.set(d)

    @staticmethod
    def from_list(gears_list):
        rv = GearResults()

        total_list = []
        near_list = []
        center_list = []
        far_list = []

        # seperate locations
        for gears in gears_list:
            totals = [0, 0]
            nears = [0, 0]
            centers = [0, 0]
            fars = [0, 0]
            for gear in gears:
                if gear.location == 'near':
                    if gear.placed:
                        totals[0] += 1
                        nears[0] += 1
                    else:
                        totals[1] += 1
                        nears[1] += 1
                elif gear.location == 'center':
                    if gear.placed:
                        totals[0] += 1
                        centers[0] += 1
                    else:
                        totals[1] += 1
                        centers[1] += 1
                elif gear.location == 'far':
                    if gear.placed:
                        totals[0] += 1
                        fars[0] += 1
                    else:
                        totals[1] += 1
                        fars[1] += 1
            total_list.append(totals)
            near_list.append(nears)
            center_list.append(centers)
            far_list.append(fars)

        rv.total = GearLocationResults.from_list(total_list)
        rv.near = GearLocationResults.from_list(near_list)
        rv.center = GearLocationResults.from_list(center_list)
        rv.far = GearLocationResults.from_list(far_list)

        return rv
