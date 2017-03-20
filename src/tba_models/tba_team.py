from data_models.data_model import DataModel


class TBATeam(DataModel):
    def __init__(self, d):
        self.address = ""
        self.city = ""
        self.gmaps_place_id = ""
        self.gmaps_url = ""
        self.home_championship = {}
        self.key = ""
        self.lat = 0
        self.lng = 0
        self.location_name = ""
        self.motto = ""
        self.name = ""
        self.nickname = ""
        self.postal_code = ""
        self.rookie_year = 0
        self.state_prov = ""
        self.team_number = 0
        self.website = ""
        self.set(d)
