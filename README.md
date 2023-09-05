# External database package

## Set up
1. Create a new environment, e.g., using conda
```bash
conda create -n bw2extdb
```
2. Acitvate the environment
```bash
cond activate bw2extdb
```
3. Install pip in conda
```bash
conda install pip
```
4. Install the `bw2extdb` package from git
```bash
pip install git+https://github.com/Blowgren/bw2extdb@main
```

## Structure
The current package consists of:
- The core backend which is the sub-package ```exportImport```, consisting of an exporting module ```exporter``` and and importer module ```importer```. Both modules are self built and orientate themselves after the workflow of brightway importer and exporter classes. 
- An app which works as a GUI for the importing and exporting routine found in the ```app``` module. 
- Example scripts found in ```examples```
- The start of a testing structure in ```tests```

## App
The app is an interface and GUI which helps the user to apply the functions for importing and exporting data. The same functions can also be called with a jupyter notebook.

To start the app:
1. start a terminal/bash
2. activate the Conda environment where this package is installed
3. start the app directly with th bash-command

```bash
bw2extdb
```


## Concept
The general idea is to:
1. Export LCI databases (including uncertainty and parameters) from BW created using AB to an external database
2. Having full control over the external database (structure, communication, versioning, access, aso.)
3. subsequently import that data to BW/AB.

I tried to keep as close to the BW code as possible so I built a python package (depending on bw) which:

1. Exports the data from a specified BW project and database and checks if the data upholds a predefined format.
    - The code is based on the CSV export (https://github.com/brightway-lca/brightway2-io/blob/main/bw2io/export/csv.py) and stores it in object relational mappers in memory using predefined type classes for the activities, exchanges, meta-data and parameters
2. Uploads/writes the checked data to an external database.
    - The ORM are built with `sqlmodel` package which combines `SQLAlchemy` and `Pydantic` and can easily be wrapped into an API using `fastAPI`. With SQLAlchemy the communication to any SQL datbase is possible, e.g. MicrosoftSQL, PostgreSQL, MySQL, Oracle and SQLite, the database is defined in the engine.
3. Imports the data with the same logic as the CSV or Excel importer.
    - The code is inherits the mporters.base_lci (https://github.com/brightway-lca/brightway2-io/blob/main/bw2io/importers/base_lci.py) where new methods are written for 'process_activities' and 'get_database'
4. In the last step the exchanges are linked to the relevant background databases (e.g. EcoInvent and biosphere3) and written to the database (.write_database)
    - Using all the provided matching and strategies methods provided in bw2io, as normally done when importing databases.

I have built a simple web-app using streamlit as a GUI for the user to the importing and exporting methods. The same workflow can also be done calling the code in a python script or jupyter notebook.

## Development ideas:
- https://fastapi.tiangolo.com/tutorial/sql-databases/
    - using SQLAlchemy 
    - using pydantic
    - using restAPI
- completely stand alone version: https://github.com/tiangolo/full-stack-fastapi-postgresql
- infromation about ORM: https://www.fullstackpython.com/object-relational-mappers-orms.html
- potential Docker file for Postgres and sql model migration: https://github.com/testdrivenio/fastapi-sqlmodel-alembic