from sqlalchemy.engine.base import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import SQLModel, create_engine

from .models import *

def create_MSsql_engine(user, password, server, database) -> Engine:
    engine = create_engine(f'mssql+pyodbc://{user}:{password}@{server}/{database}')
    # engine = create_engine('mssql+pyodbc://VITODB24DEV/SesamLCA')
    return engine


def create_sqlite_engine(sqlite_file_path:str) -> Engine:
    sqlite_url = f"sqlite:///{sqlite_file_path}"
    engine = create_engine(sqlite_url, echo=True)
    return engine

def create_inmemory_sqlite_engine() -> Engine:
    sqlite_url = "sqlite://"
    engine = create_engine(sqlite_url, echo=True)
    return engine

def test_connection(engine):
    try:
        engine.connect()
        print("connected successfully to database")
    except SQLAlchemyError as err:
        print('could not connect to database successfully')
        print("error", err.__cause__) 

def create_db_and_tables(engine):
    SQLModel.metadata.create_all(engine)