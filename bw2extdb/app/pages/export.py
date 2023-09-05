import streamlit as st
import sys
from io import StringIO
import bw2data
from bw2extdb.exportImport import exporter

class OutputCapture:
    def __init__(self):
        self._output = StringIO()

    def write(self, text):
        self._output.write(text)

    def get_output(self):
        return self._output.getvalue()


st.header('SESAM LCI data export')
project = st.selectbox("Select Project", [project[0] for project in bw2data.projects.report()])
selected_project = st.session_state.get('selected_project', None)

if project != selected_project:
    st.session_state.selected_project = project
    st.session_state.selected_databases = []
bw2data.projects.set_current(project)
selected_databases = st.multiselect("Select Databases", bw2data.databases)

# ATTN: add warning if no data is specified
project_description = st.text_area("Project Description")
project_name = st.text_input("Project Name")
final_date = st.date_input("Final Date")
keywords_raw = st.text_input("Keywords (seperate by comma)")
user_name = st.selectbox("select your user name", ["admin", "test"])
# split  keyword string into keywords
keywords = keywords_raw.split(',')

if st.button("Export"):
    # Capture the terminal output
    capture = OutputCapture()
    sys.stdout = capture

    # try:
    LCIExporter = exporter.LCIExporter(project_name=project, databases=selected_databases)
    processactivities, emissionactivities = LCIExporter.extract_lci_data()
    project_metadata = LCIExporter.create_metadata(
        project_name, 
        project_final_date=final_date, 
        description=project_description,
        keywords=keywords,
        user_name=user_name,
        )
    LCIExporter.export_to_sql(process_activities=processactivities, projectmetadatacreate=project_metadata, emissionactivities=emissionactivities)
    # except Exception as e:
    #     print(f'Error: {str(e)}')

    # Reset the standard output
    sys.stdout = sys.__stdout__

    output = capture.get_output()
    st.text_area("Terminal Output", value=output)