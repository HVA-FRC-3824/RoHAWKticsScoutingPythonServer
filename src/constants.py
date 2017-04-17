class Constants:
    OUR_TEAM_NUMBER = 3824

    GEAR_PLACEMENT_LOCATION_NEAR = "near"
    GEAR_PLACEMENT_LOCATION_CENTER = "center"
    GEAR_PLACEMENT_LOCATION_FAR = "far"
    GEAR_LOCATIONS = [GEAR_PLACEMENT_LOCATION_NEAR,
                      GEAR_PLACEMENT_LOCATION_CENTER,
                      GEAR_PLACEMENT_LOCATION_FAR]
    GEAR_LOCATIONS_WITH_TOTAL = ['total',
                                 GEAR_PLACEMENT_LOCATION_NEAR,
                                 GEAR_PLACEMENT_LOCATION_CENTER,
                                 GEAR_PLACEMENT_LOCATION_FAR]

    ENDGAME_CLIMB_KEY = "endgame_climb"
    ENDGAME_CLIMB_NO_ATTEMPT_KEY = "no_attempt"
    ENDGAME_CLIMB_NO_ATTEMPT = "No attempt"
    ENDGAME_CLIMB_DID_NOT_FINISH_IN_TIME_KEY = "did_not_finish_in_time"
    ENDGAME_CLIMB_DID_NOT_FINISH_IN_TIME = "Did not finish in time"
    ENDGAME_CLIMB_ROBOT_FELL_KEY = "robot_fell"
    ENDGAME_CLIMB_ROBOT_FELL = "Robot fell"
    ENDGAME_CLIMB_SUCCESSFUL_KEY = "successful"
    ENDGAME_CLIMB_SUCCESSFUL = "Successful"
    ENDGAME_CLIMB_CREDITED_THROUGH_FOUL = "credited_through_foul"
    ENDGAME_CLIMB_CREDITED_THROUGH_FOUL_KEY = "Credited through foul"
    ENDGAME_CLIMB_OPTIONS = {ENDGAME_CLIMB_SUCCESSFUL: ENDGAME_CLIMB_SUCCESSFUL_KEY,
                             ENDGAME_CLIMB_ROBOT_FELL: ENDGAME_CLIMB_ROBOT_FELL_KEY,
                             ENDGAME_CLIMB_DID_NOT_FINISH_IN_TIME: ENDGAME_CLIMB_DID_NOT_FINISH_IN_TIME_KEY,
                             ENDGAME_CLIMB_NO_ATTEMPT: ENDGAME_CLIMB_NO_ATTEMPT_KEY,
                             ENDGAME_CLIMB_CREDITED_THROUGH_FOUL: ENDGAME_CLIMB_CREDITED_THROUGH_FOUL_KEY}

    ENDGAME_CLIMB_TIME_KEY = "endgame_climb_time"
    ENDGAME_CLIMB_TIME_N_A = "N/A"

    shared_state = {}

    def __init__(self):
        self.__dict__ = self.shared_state
        if hasattr(self, "instance"):
            self.team_numbers = []
            self.number_of_matches = -1
            self.scout_names = []
            self.instance = True
