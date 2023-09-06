import streamlit as st
import sys
from io import StringIO
import bw2data
from bw2extdb.exportImport import importer
from bw2extdb.exportImport.crud import Crud


class OutputCapture:
    def __init__(self):
        self._output = StringIO()

    def write(self, text):
        self._output.write(text)

    def get_output(self):
        return self._output.getvalue()

st.header('SQL database import')

## Specify the bw project and database to be imported
if 'engine' not in st.session_state:
    st.error('Please connect to a database first')
    st.session_state.engine = None
else:
    crud = Crud(st.session_state.engine)
    projectmetadatalist = crud.read_all_projectmetadata()
    project_names = [projectmetadata.project_name for projectmetadata in projectmetadatalist]
database = st.selectbox("Select remote database", project_names)
project = st.selectbox("Select Brightway project to import to", [project[0] for project in bw2data.projects.report()])
bw2data.projects.set_current(project)
databases = list(bw2data.databases)
# ATTN: print the database dependencies

## Select how the imported database should be linked
link_biosphere = st.checkbox("Link Biosphere")
if link_biosphere:
    biosphere_dbs = st.multiselect('Select Technosphere Databases',databases)
    biosphere_matching_list = []
    for biosphere_db in biosphere_dbs:
        matching = {}
        matching['name'] = biosphere_db
        col1, col2 = st.columns(2)
        # The database to be matched with
        with col1:
            st.markdown(f'Database \n\n **{biosphere_db}**')
        # On what fields the imported and the external database should be linked
        with col2:
            matching['fields'] = st.multiselect('Select the Fields for Matching', ['name', 'location', 'unit', 'reference product', 'code'], key=biosphere_db+'multiselect')
        biosphere_matching_list.append(matching)
link_technosphere = st.checkbox("Link Technosphere Internally")
link_production = st.checkbox("Link Production Internally")
link_technosphere_ext = st.checkbox("Link Technosphere Externally")
ext_technosphere_dbs = []
# Linking to a user specified bw database
if link_technosphere_ext:
    # Get the list of available databases and remove the current database and the biosphere3 database
    if 'biosphere3' in databases:
        databases.remove('biosphere3')
    if database in databases:
        databases.remove(database)
    ext_technosphere_dbs = st.multiselect('Select Technosphere Databases',databases)
    ext_technosphere_matching_list = []
    # For each of the selected databases specify how the matching should be
    for ext_technosphere_db in ext_technosphere_dbs:
        matching = {}
        matching['name'] = ext_technosphere_db
        col1, col2, col3 = st.columns(3)
        # The database to be matched with
        with col1:
            st.markdown(f'Database \n\n **{ext_technosphere_db}**')
        # What kind/type that database is
        with col2:
            matching['kind'] = st.selectbox("Select Database Kind", ['technosphere','production','biosphere'], key=ext_technosphere_db)
        # On what fields the imported and the external database should be linked
        with col3:
            matching['fields'] = st.multiselect('Select the Fields for Matching', ['name', 'location', 'unit', 'reference product', 'code'], key=ext_technosphere_db+'multiselect')
        ext_technosphere_matching_list.append(matching)

## Import and match the selected database
if st.button("Import"):
    # Capture the terminal output
    capture = OutputCapture()
    sys.stdout = capture
    try:
        if 'engine' not in st.session_state:
            st.error('Please connect to a database first')
        else:
            LCIExporter_app = importer.LCIImporterSql(project_name=project, project_database_name=database, engine=st.session_state.engine)
            print('statistics after initial data loading:')
            LCIExporter_app.statistics()
            if link_biosphere:
                for matching in biosphere_matching_list:
                    LCIExporter_app.match_database(matching['name'], fields=matching['fields'], kind='biosphere')
                    print('\nstatistics of imported data after linking to {}:'.format(matching['name']))
                    LCIExporter_app.statistics()
            if link_technosphere:
                LCIExporter_app.match_database(kind="technosphere", fields=["code"])
                print('\nstatistics of imported data after linking the technosphere exchanges internally:')
                LCIExporter_app.statistics()
            if link_production:
                LCIExporter_app.match_database(kind="production", fields=["code"])
                print('\nstatistics of imported data after linking the production exchanges internally:')
                LCIExporter_app.statistics()
            if link_technosphere_ext:
                for matching in ext_technosphere_matching_list:
                    LCIExporter_app.match_database(matching['name'], fields=matching['fields'], kind=matching['kind'])
                    print('\nstatistics of imported data after linking to {}:'.format(matching['name']))
                    LCIExporter_app.statistics()
            # Reset the standard output
            if LCIExporter_app.statistics()[2] == 0:
                print('The complete database could be matched and the database is being written.')
                sys.stdout = sys.__stdout__
                LCIExporter_app.write_database()
            else:
                print("The database could not be written because there are unlinked exchanges.")
                # ATTN: There are some bigger probelms with the write_excel
                excel_path = LCIExporter_app.write_excel(only_unlinked=True)
                st.markdown(f'The excel file has been written to: \n{excel_path}')
    except Exception as e:
        print(f'Error: {str(e)}')
    # Reset the standard output
    sys.stdout = sys.__stdout__
    output = capture.get_output()
    st.text_area("Terminal Output", value=output)
