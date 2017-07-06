import csv
import argparse

from database import Database
from data_models.team_match_data import TeamMatchData
from data_models.team_calculated_data import TeamCalculatedData
from decorator import attr_check, type_check, void


@attr_check
class CSVExporter:
    @type_check
    def __init__(self, event_id: str):
        self.database = Database(event_id)

    @type_check
    def export_team_match_data(self, filename: str) -> void:
        with open(filename, 'w') as csvfile:
            fieldnames = TeamMatchData.get_csv_field_names()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for key, tmd in self.database.get_all_team_match_data().items():
                writer.writerow(tmd.to_csv_row())

    @type_check
    def export_team_calculated_data(self, filename: str) -> void:
        with open(filename, 'w') as csvfile:
            fieldnames = TeamCalculatedData.get_csv_field_names()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for team_number, tcd in self.database.get_all_team_calculated_data().items():
                writer.writerow(tcd.to_csv_row())


if __name__ == '__main__':
    # Collect command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-e", "--event_key", required=True, help="Event key used by the blue alliance")
    args = vars(ap.parse_args())

    csv_exporter = CSVExporter(args['event_key'])

    csv_exporter.export_team_match_data(args['event_key'] + "_match_data.csv")
    csv_exporter.export_team_calculated_data(args['event_key'] + "_calc_data.csv")