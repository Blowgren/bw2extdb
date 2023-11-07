import streamlit as st
import bw2extdb.exportImport.database as database
import os
import sqlite3
from urllib.request import pathname2url
from sqlalchemy.engine.base import Engine
from enum import Enum

class SQLtype(str,Enum):
    SQlite = 'SQLite'
    PostgreSQL = 'PostgreSQL'
    PostgreSQLmigration = 'PostgresSQL with migration'
    MicrosoftSQL = 'MicrosoftSQL'
    from_URL = 'from URL'

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


st.header('SQL database connection')

st.markdown(
    "Here you can conncect to the SQL database where you want to import and export the data to"
)

sql_type_input = st.selectbox(label='SQL database type', options=SQLtype.SQlite.list())

@st.cache_resource
def create_sqlite_engine(sqlite_file_path:str) -> Engine:
    engine = database.create_sqlite_engine(sqlite_file_path)
    database.create_db_and_tables(engine)
    return engine

@st.cache_resource
def create_engine_from_url(sqlite_file_path:str) -> Engine:
    engine = database.create_engine_from_url(sqlite_file_path)
    database.create_db_and_tables(engine)
    return engine

@st.cache_resource
def create_engine_postgreSQL(user:str, password:str, server:str, database_name:str) -> Engine:
    engine = database.create_PostgreSQL_engine(user, password, server, database_name)
    database.create_db_and_tables(engine)
    return engine

@st.cache_resource
def create_engine_postgreSQL_with_migration(user:str, password:str, server:str, database_name:str) -> Engine:
    engine = database.create_PostgreSQL_engine(user, password, server, database_name)
    database.init_db(engine)
    return engine

match sql_type_input:
    case SQLtype.SQlite:
        sqlite_path = st.text_input(label='Path to local SQLite database file.')
        new_sqlite_database = st.checkbox('Create a new SQLite Database with the specified path')

    case SQLtype.from_URL:
        url = st.text_input(label='URL for database connection:', placeholder='dialect+driver://username:password@host:port/database')

    case SQLtype.PostgreSQL | SQLtype.PostgreSQLmigration:
        user = st.text_input('user', value='bgxpifkr')
        password = st.text_input('password', type='password', value='rdCZJHrLAXUxw5uuKPHzi72TqJsYakgg')
        server = st.text_input('server', value='dumbo.db.elephantsql.com')
        database_name = st.text_input('database', value='bgxpifkr')        

    case _:
        st.error('This type has not been implemented yet.')

connect = st.button('connect')
if connect:
    match sql_type_input:
        case SQLtype.SQlite:
            if not os.path.isfile(sqlite_path) and not new_sqlite_database:
                st.warning('there is no sqlite database at that path')
            else:
                connection = True
                if not new_sqlite_database:
                    try:
                        con = sqlite3.connect('file:{}?mode=rw'.format(pathname2url(sqlite_path)), uri=True)
                    except sqlite3.OperationalError:
                        st.warning('The specified file is not a sqlite database.')
                        connection = False
                if connection:
                    engine = create_sqlite_engine(sqlite_path)
                    st.session_state.engine = engine
                    if database.test_connection(engine):
                        st.success('connected to SQL database')
                    else:
                        st.error('could not connect to SQL database')

        case SQLtype.from_URL:
            if not url:
                st.warning('Please specify the URL')
            else:
                engine = create_engine_from_url(url)
                st.session_state.engine = engine
                if database.test_connection(engine):
                    st.success('connected to SQL database')
                else:
                    st.error('could not connect to SQL database')

        case SQLtype.PostgreSQL:
            if not (user and password and server and database_name):
                st.warning('Please specify user, password, server and database name')
            else:
                engine = create_engine_postgreSQL(user, password, server, database_name)
                st.session_state.engine = engine
                if database.test_connection(engine):
                    st.success('connected to SQL database')
                else:
                    st.error('could not connect to SQL database')

        case SQLtype.PostgreSQLmigration:
            if not (user and password and server and database_name):
                st.warning('Please specify user, password, server and database name')
            else:
                engine = create_engine_postgreSQL_with_migration(user, password, server, database_name)
                st.session_state.engine = engine
                if database.test_connection(engine):
                    st.success('connected to SQL database')
                else:
                    st.error('could not connect to SQL database')

        case _:
            st.error('This type has not been implemented yet.')