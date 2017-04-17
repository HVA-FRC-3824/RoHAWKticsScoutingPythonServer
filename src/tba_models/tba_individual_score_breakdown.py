from data_models.data_model import DataModel


class TBAIndividualScoreBreakdown(DataModel):
    def __init__(self, d=None):
        self.adjustPoints = 0
        self.autoFuelHigh = 0
        self.autoFuelLow = 0
        self.autoFuelPoints = 0
        self.autoMobilityPoints = 0
        self.autoPoints = 0
        self.autoRotorPoints = 0
        self.foulCount = 0
        self.foulPoints = 0
        self.kPaBonusPoints = 0
        self.kPaRankingPointAchieved = False
        self.robot1Auto = ""
        self.robot2Auto = ""
        self.robot3Auto = ""
        self.rotor1Auto = False
        self.rotor1Engaged = False
        self.rotor2Auto = False
        self.rotor2Engaged = False
        self.rotor3Engaged = False
        self.rotor4Engaged = False
        self.rotorRankingPointAchieved = False
        self.techFoulCount = 0
        self.teleopFuelHigh = 0
        self.teleopFuelLow = 0
        self.teleopFuelPoints = 0
        self.teleopPoints = 0
        self.teleopRotorPoints = 0
        self.teleopTakeoffPoints = 0
        self.totalPoints = 0
        self.touchpadFar = ""
        self.touchpadMiddle = ""
        self.touchpadNear = ""
        if d is not None:
            self.set(d)
