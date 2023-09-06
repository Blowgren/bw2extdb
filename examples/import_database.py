import bw2extdb.exportImport.importer as importer
import bw2extdb.exportImport.database as database
import bw2data
from bw2io import bw2setup
import pathlib

project_name = 'import_test'
project_database_name = "test exporting using Mobility example"
if project_name in bw2data.projects:
    bw2data.projects.delete_project(project_name, delete_dir=True)
bw2data.projects.set_current(project_name)
bw2setup()

""" Create the sql engine and set up database """
sqlite_file_path =  pathlib.Path(__file__).parent / 'example_database.db'
sqlite_file_path_abs = sqlite_file_path.resolve()._str
engine = database.create_sqlite_engine(sqlite_file_path_abs)
database.create_db_and_tables(engine)

""" Extract the data from the sql database to brightway type data """
LCIImporter = importer.LCIImporterSql(project_name, project_database_name, engine)

""" Link the database """
print("statistics of imported data:")
LCIImporter.statistics()
LCIImporter.match_database("biosphere3", fields=["code"], kind="biosphere")
print("statistics of imported data after linking to biosphere database:")
LCIImporter.statistics()
LCIImporter.match_database(fields=['reference product', 'unit', 'location', 'name'], kind='biosphere')
print("statistics of imported data after linking the biosphere exchanges internally:")
LCIImporter.statistics()
LCIImporter.match_database(kind="production", fields=["code"])
print("statistics of imported data after linking the production exchanges internally:")
LCIImporter.statistics()
LCIImporter.match_database(kind="technosphere", fields=["code"])
print("statistics of imported data after linking the technosphere exchanges internally:")
LCIImporter.statistics()
# LCIImporter.drop_unlinked(i_am_reckless=True)
# # LCIImporter.write_unlinked('test') #ATTN: This does not work something is wrong in the code
if LCIImporter.statistics()[2] == 0:
    LCIImporter.write_database()
else:
    print("There are unlinked exchanges.")
    LCIImporter.write_excel()
print("end")