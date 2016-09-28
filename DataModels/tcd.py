from .data_model import DataModel


class TCD(DataModel):
    def __init__(self, **kwargs):
        # Autonomous

        # Teleop

        # Endgame

        # Post Match
        self.no_show = None
        self.stopped_moving = None
        self.dq = None

        # Fouls
        self.fouls = None
        self.tech_fouls = None
        self.yellow_cards = None
        self.red_cards = None

        # Qualitative
        self.zscore_speed = 0.0
        self.rank_speed = -1

        self.zscore_torque = 0.0
        self.rank_torque = -1

        self.zscore_control = 0.0
        self.rank_control = -1

        self.zscore_defense = 0.0
        self.rank_defense = -1

        self.__dict__.update(kwargs)
