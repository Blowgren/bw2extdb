import streamlit as st
import bw2data

def main():
    bw2data.projects.set_current("default")  # Set the default Brightway project

    st.title("Brightway Import Export App")
    st.markdown(
        """
            This app is a GUI for the use of the python package `bw2extdb`. There are two main functionalities **export** and **import**. 
            They can be accessed in the menu and are described in more detail below.
            ## Exporter
            Exports one or multiple databases of a brightway project into an external SQL database.
            ## Importer
            Imports a database from an external SQL database, which is created using the **exporter** workflow.
        """
    )
    # st.sidebar.markdown("# Main page")

if __name__ == "__main__":
    main()
