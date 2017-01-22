from .data_model import DataModel


class Shots(DataModel):
    def __init__(self, **kwargs):
        self.high_goal_made = 0
        self.high_goal_missed = 0
        self.low_goal_made = 0
        self.low_goal_missed = 0

        self.set(**kwargs)
