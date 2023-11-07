import pathlib
from sqlalchemy.engine.base import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import SQLModel, create_engine
from alembic.config import Config
from alembic import command

from .models import *

def create_MSsql_engine(user, password, server, database_name) -> Engine:
    engine = create_engine(f'mssql+pyodbc://{user}:{password}@{server}/{database_name}')
    # engine = create_engine('mssql+pyodbc://VITODB24DEV/SesamLCA')
    return engine

def create_PostgreSQL_engine(user, password, server, database_name) -> Engine:
    engine = create_engine(f'postgresql+psycopg2://{user}:{password}@{server}/{database_name}')
    return engine

def create_engine_from_url(url:str) -> Engine:
    engine = create_engine(url)
    return engine

def create_sqlite_engine(sqlite_file_path:str) -> Engine:
    sqlite_url = f"sqlite:///{sqlite_file_path}"
    engine = create_engine(sqlite_url, echo=True)
    return engine

def create_inmemory_sqlite_engine() -> Engine:
    sqlite_url = "sqlite://"
    engine = create_engine(sqlite_url, echo=True)
    return engine

def test_connection(engine) -> bool:
    connection_success = True
    try:
        engine.connect()
        print("connected successfully to database")
    except SQLAlchemyError as err:
        print('could not connect to database successfully')
        print("error", err.__cause__) 
        connection_success = False
    return connection_success

def create_db_and_tables(engine):
    SQLModel.metadata.create_all(engine)

def init_db(engine):
    alembicini_path = pathlib.Path(__file__).parent.parent.parent / 'alembic.ini'
    alembic_cfg = Config(alembicini_path)
    with engine.begin() as connection:
        alembic_cfg.attributes['connection'] = connection
        command.upgrade(alembic_cfg, "head")