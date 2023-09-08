import bw2extdb.exportImport.exporter as exporter
import bw2extdb.exportImport.database as database

import datetime
import os
import pathlib

import bw2io
import bw2data

""" Download and set up the database for testing """
project_name = 'bw2extdb_test'
if project_name in bw2data.projects:
    bw2data.projects.delete_project(project_name, delete_dir=True)
bw2data.projects.set_current(project_name)
bw2io.bw2setup()
bw2io.data.add_example_database(overwrite=False)

""" Define the information for the testing """
dbs = ['Mobility example']
biosphere_version = '3.8'
dataset_final_date = datetime.date(2022,5,11)

""" delete the database if it exists """
# Set the SQLlite path
sqlite_file_path =  pathlib.Path(__file__).parent / 'example_database.db'
sqlite_file_path_abs = sqlite_file_path.resolve()._str
# Delete the SQL database if it already exists
if os.path.isfile(sqlite_file_path_abs):
    os.remove(sqlite_file_path_abs)

""" Create the sql engine and set up database """
engine = database.create_sqlite_engine(sqlite_file_path_abs)
database.create_db_and_tables(engine)

""" Export the LCI data from brightway to memory """
# Initialize the LCIexporter with the bw project name and a list of bw databases
LCIExporter = exporter.LCIExporter(project_name=project_name, databases=dbs, engine=engine, biosphere_version=biosphere_version)
# Extract the data from the databases and put it into new format
processactivities, emissionactivities = LCIExporter.extract_lci_data()
# Create the metadata for the extracted database dataset
datasetmetadata = LCIExporter.create_metadata(
    dataset_name='Mobility example', 
    dataset_final_date=dataset_final_date, 
    description='',
    user_name='test_user',
    keywords_input=['test', 'Mobility', 'example']
    )

""" Test the completeness of the data for export """
LCIExporter.check_activities_completeness(processactivities, datasetmetadata, emissionactivities=emissionactivities)

""" Export the LCI data to a SQLite database """
LCIExporter.export_to_sql(processactivities, datasetmetadata, emissionactivities=emissionactivities)
print('end')