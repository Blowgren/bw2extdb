import streamlit as st
import sys
from io import StringIO
import bw2data
from bw2extdb.exportImport import exporter
import re

class OutputCapture:
    def __init__(self):
        self._output = StringIO()

    def write(self, text):
        self._output.write(text)

    def get_output(self):
        return self._output.getvalue()


st.header('SQL database export')
project = st.selectbox("Select Project", [project[0] for project in bw2data.projects.report()])
selected_project = st.session_state.get('selected_project', None)

if project != selected_project:
    st.session_state.selected_project = project
    st.session_state.selected_databases = []
bw2data.projects.set_current(project)
selected_databases = st.multiselect("Select Databases", bw2data.databases)
biosphere_version = st.selectbox('biosphere version', [None, '3.8', '3.9'])
# ATTN: add warning if no data is specified
dataset_description = st.text_area("Dataset Description")
dataset_name = st.text_input("Dataset Name")
final_date = st.date_input("Final Date")
keywords_raw = st.text_input("Keywords (seperate by comma)")
user_email_addres = st.text_input("Enter your email address")
regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
if user_email_addres:
    if not (re.fullmatch(regex, user_email_addres)):
        st.error("Invalid Email")

# split  keyword string into keywords
keywords = keywords_raw.split(',')

if st.button("Export"):
    # Capture the terminal output
    capture = OutputCapture()
    sys.stdout = capture

    # try:
    if 'engine' not in st.session_state:
        st.error('Please connect to a database first')
    else:
        LCIExporter = exporter.LCIExporter(project_name=project, databases=selected_databases, engine=st.session_state.engine, biosphere_version=biosphere_version)
        processactivities, emissionactivities = LCIExporter.extract_lci_data()
        datasetmetadata = LCIExporter.create_metadata(
            dataset_name, 
            dataset_final_date=final_date, 
            description=dataset_description,
            keywords_input=keywords,
            user_email_addres=user_email_addres,
            )
        try:
            LCIExporter.export_to_sql(processactivities=processactivities, datasetmetadata=datasetmetadata, emissionactivities=emissionactivities)
            export_success = True
        except Exception as e:
            print(f'Error: {str(e)}')
            export_success = False
        if export_success:
            st.success("Dataset exported successfully")
        else:
            st.error("Dataset was not exported successfully, check terminal output below")
        # Reset the standard output
        sys.stdout = sys.__stdout__

        output = capture.get_output()
        st.text_area("Terminal Output", value=output)