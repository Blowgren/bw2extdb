import pathlib

from bw2extdb.exportImport.models import *
import bw2extdb.exportImport.database  as database

sqlite_file_path =  pathlib.Path(__file__).parent / 'example_database.db'
engine = database.create_sqlite_engine(sqlite_file_path.resolve()._str)
database.create_db_and_tables(engine)