from datetime import date
import atexit
import shutil
import warnings
import pandas as pd
import copy
import os
import shutil
from typing import List, Tuple, Dict, Any, Union, Literal
from sqlalchemy.engine.base import Engine

import bw2data
import bw2io
from bw2data.filesystem import safe_filename

from .models import *
from .crud import Crud
from .database import create_inmemory_sqlite_engine, create_db_and_tables
from .importer import LCIImporterSql

# TO-DO:
# - go through the exporter and write out the extraction processes and all the underlying assumptions
# - go through and implement the bullet points from the teams meetings: 20230612_SESAME_database_team_presentation
# - check why the write `write_unlinked` method does not work


class LCIExporter:
    """
    Export Life Cycle Inventory (LCI) data from Brightway2 databases to a format compatible with the current application.

    This class allows exporting LCI data from specified Brightway2 databases to a format that can be used in the current application.
    It supports exporting activities, their exchanges, and related metadata.

    Args:
        project_name (str): The name of the current project in the application.
        databases (List[str]): A list of Brightway2 database names to be exported.

    Attributes:
        project_name (str): The name of the current project in the application.
        databases (List[str]): A list of Brightway2 database names to be exported.
        biosphere_version (str): The version of the Brightway2 Biosphere3 database used for export.

    Methods:
        extract_lci_data(self) -> List[Activity]:
            Extracts activities, their exchanges, and related metadata from the specified Brightway2 databases.

        check_activities_completeness(self, activities: List[Activity]):
            Performs checks on the completeness of the exported activities.

        check_background_database_dependency(self) -> List[str]:
            Checks and returns a list of background databases on which the exported databases depend.

        create_metadata(
            self,
            dataset_name: str,
            dataset_final_date: datetime,
            description: str,
            user_email_addres: str,
            keywords_input: Optional[List] = [],
        ) -> DatasetMetadata:
            Creates metadata for the exported data and dataset.

        check_datasetmetadata_completeness(self, datasetmetadata: DatasetMetadata):
            Performs checks on the completeness of the dataset metadata.

        create_version(self) -> float:
            Generates and returns a version number for the exported data format.

    Raises:
        Exception: If an unknown exchange type is encountered during extraction.

    Examples:
        # Initialize the LCIExporter
        exporter = LCIExporter(project_name="MyLCIProject", databases=["db1", "db2"])

        # Extract LCI data
        activities_data = exporter.extract_lci_data()

        # Create dataset metadata
        datasetmetadata = exporter.create_metadata(
            dataset_name="MyLCIProject",
            dataset_final_date=datetime.date(2023, 8, 1),
            description="A sample LCI dataset for demonstration.",
            user_email_addres="john.doe@protonmail.com",
        )

        # Perform completeness checks
        exporter.check_activities_completeness(activities_data)
        exporter.check_datasetmetadata_completeness(datasetmetadata)

    """

    
    def __init__(self, project_name: str, databases: list[str], engine: Engine, biosphere_version: Optional[Union[Literal['3.8'], Literal['3.9']]] = None):
        self.engine = engine
        self.project_name = project_name
        self.databases = databases
        self.biosphere_version = self._get_biosphere_version(biosphere_version)
        self.crud = Crud(engine)
        bw2data.projects.set_current(project_name)

    @staticmethod
    def _get_biosphere_version(biosphere_version:Optional[Union[Literal['3.8'], Literal['3.9']]] = None) -> str:
        """
        Currently the biosphere version needs to be set manually, because there is no generalized way to do this.

        Read more about it here: https://github.com/brightway-lca/brightway2-io
        """
        if biosphere_version != None and biosphere_version not in ['3.8', '3.9']:
            raise Exception(f'The specified biosphere version: {biosphere_version} is not valid, it must be either 3.8 or 3.9')
        
        # ATTN: The user must export the data with the same bw2io version as they created the biosphere3 database with
        # bwioversion_current =  ".".join([str(num) for num in bw2io.__version__])
        return biosphere_version

    def extract_lci_data(self, databases:List[str]=[]) -> Tuple[List[ProcessActivityCreate], List[EmissionActivityCreate]]:
        """
        Extracts activities, their exchanges, and related metadata from the specified Brightway2 databases.

        Returns:
            List[ProcessActivityCreate]: A list of Process Activity objects representing the exported LCI data.
            List[EmissionActivityCreate]: A list of Emission Activity objects representing the exported LCI data.
        """
        processactivities = []
        emissionactivities = []
        if not databases:
            databases = self.databases
        for db_name in databases:
            print(f"Exporting database: {db_name}")
            # Connect to the database in the project
            db = bw2data.Database(db_name)
            # Export activities
            for act in db:
                # ATTN: Check if production amount is 1
                # The type is also assumed to be process if no type is specified (None)
                if act.get("type") == "process" or act.get("type") == None:
                    processactivity = ProcessActivityCreate(
                        code=act.get("database") + act.get("code"), # The code is only unique if paired with the database name
                        database_old = act.get("database"),
                        name=act.get("name"),
                        location=act.get("location"),
                        reference_product=act.get("reference product"),
                        unit=act.get("unit"),
                        type='process',
                        comment=act.get("comment"),
                        biosphere_version=self.biosphere_version,
                    )
                    process_activity_variables = ['code', 'database', 'name', 'location', 'reference product', 'unit', 'type', 'comment']
                    process_activity_variables_diff = list(set(act.as_dict().keys()) - set(process_activity_variables))
                    if len(process_activity_variables_diff) > 0:
                        warnings.warn('For process activity {} in {} will the following variables not be exported \n {}'. format(act.get("code"), act.get("database"), process_activity_variables_diff))
                    # Export exchanges
                    biosphereexchanges = []
                    technosphereexchanges = []
                    for exc in act.exchanges():
                        # ATTN: raise a warning that only the specified variables will be extracted (check if more are specified)
                        if exc.get("type") == "technosphere" or exc.get("type") == "production":
                            technosphereexchange = TechnosphereExchangeCreate(
                                # ATTN: the output code is setup by combining the code and the database since multiple databases are merged
                                output_code=exc.output.get("database") + exc.output.get("code"),
                                location=exc.input.get("location"),
                                unit=exc.input.get("unit"),
                                name=exc.input.get("name"),
                                input_code=exc.input.get("database") + exc.input.get("code"),
                                reference_product=exc.input.get("reference product"),
                                amount=exc.get("amount"),
                                type=exc.get("type"),
                                formula=exc.get("formula"),  # ATTN: this needs to be checked for parametrized data
                                # ATTN: not tested with uncertainty data
                                uncertainty_type = exc.get('uncertainty type'),
                                loc = exc.get('loc'),
                                scale = exc.get('scale'),
                                shape = exc.get('shape'),
                                minimum = exc.get('minimum'),
                                maximum = exc.get('maximum'),
                            )
                            categories = []
                            for category_data in exc.input.get("categories",[]):
                                category = CategoryCreate(name=category_data)
                                categories.append(category)
                            technosphereexchange.categories = categories
                            technosphereexchanges.append(technosphereexchange)
                            exchange_variables = ['amount', 'type', 'formula', 'loc', 'scale', 'shape', 'minimum', 'maximum', 'uncertainty type']
                            exchange_variables_diff = list(set(act.as_dict().keys()) - set(exchange_variables))
                            if len(exchange_variables_diff) > 0:
                                warnings.warn('For Exchange from {} in {} to {} in {} will the following variables not be exported \n {}'. format(exc.input.get("code"), exc.input.get("database"), exc.output.get("code"), exc.output.get("database"), exchange_variables_diff))
                        elif exc.get("type") == "biosphere":
                            biosphereexchange = BiosphereExchangeCreate(
                                # ATTN: the output code is setup by combining the code and the database since multiple databases are merged
                                output_code=exc.output.get("database") + exc.output.get("code"),
                                location=exc.input.get("location"),
                                unit=exc.input.get("unit"),
                                name=exc.input.get("name"),
                                input_code=exc.input.get("code"),
                                amount=exc.get("amount"),
                                type=exc.get("type"),
                                # ATTN: not tested with uncertainty data
                                uncertainty_type = exc.get('uncertainty type'),
                                loc = exc.get('loc'),
                                scale = exc.get('scale'),
                                shape = exc.get('shape'),
                                minimum = exc.get('minimum'),
                                maximum = exc.get('maximum'),
                            )
                            categories = []
                            for category_data in exc.input.get("categories",[]):
                                category = CategoryCreate(name=category_data)
                                categories.append(category)
                            biosphereexchange.categories = categories
                            biosphereexchanges.append(biosphereexchange)
                        else:
                            raise Exception("Uknown exchange type encountered.")
                    processactivity.biosphere_exchanges = biosphereexchanges
                    processactivity.technosphere_exchanges = technosphereexchanges
                    processactivities.append(processactivity)
                elif act.get("type") == "emission":
                    emissionactivity = EmissionActivityCreate(
                        code=act.get("database") + act.get("code"), # The code is only unique if paired with the database name
                        database_old = act.get("database"),
                        name=act.get("name"),
                        location=act.get("location"),
                        unit=act.get("unit"),
                        type=act.get("type"),
                        comment=act.get("comment"),
                        biosphere_version=self.biosphere_version,
                    )
                    emissionactivities.append(emissionactivity)
                elif act.get("type") == "product":
                    raise Exception("The extraction of products has not been implemented yet.")
                else:
                    raise Exception("type {} is not known to us.".format(act.get("type")))
        print("Finished extracting the data")
        return processactivities, emissionactivities

    @staticmethod
    def create_in_memory_sqlite_database(processactivities: List[ProcessActivityCreate], datasetmetadatacreate: DatasetMetadataCreate, emissionactivities: Optional[List[EmissionActivityCreate]] = []) -> Tuple[Engine, DatasetMetadata]:
        # Creates in memory sql database
        engine_temp = create_inmemory_sqlite_engine()
        create_db_and_tables(engine_temp)
        crud_temp = Crud(engine_temp)
        datasetmetadatacreate_copy = copy.deepcopy(datasetmetadatacreate)
        datasetmetadatacreate_copy.dataset_name = '' # Use an empty name to create backwards compatability, since the uuid id code+database
        datasetmetadata = crud_temp.create_datasetmetadata(datasetmetadatacreate=datasetmetadatacreate_copy)
        processactivities_copy = copy.deepcopy(processactivities)
        emissionactivities_copy = copy.deepcopy(emissionactivities)
        crud_temp.create_process_activities(activities=processactivities_copy, datasetmetadata_id=datasetmetadata.id)
        crud_temp.create_emission_activities(activities=emissionactivities_copy, datasetmetadata_id=datasetmetadata.id)
        return engine_temp, datasetmetadata
    
    @staticmethod
    def create_temporal_copy_of_current_BW_project(temporal_project_name:str) -> str:
        # Creates temporal copy of current project
        original_project_dir = bw2data.projects.dir
        temporal_dir = bw2data.project.projects._use_temp_directory()
        atexit.register(shutil.rmtree, temporal_dir)
        bw2data.project.ProjectDataset.create(data=None, name=temporal_project_name)
        temporal_project_dir = os.path.join(bw2data.projects._base_data_dir, safe_filename(temporal_project_name))
        shutil.copytree(original_project_dir, temporal_project_dir, ignore=lambda x, y: ["write-lock"], dirs_exist_ok=True)
        return temporal_project_dir
    
    @staticmethod
    def _compare_imported_to_original_processactivities(imported_processactivities: List[ProcessActivityCreate], original_processactivities: List[ProcessActivityCreate]):
        imported_processactivities.sort(key=lambda x: x.code, reverse=True) # data needs to be sorted to check if equal
        original_processactivities.sort(key=lambda x: x.code, reverse=True) # data needs to be sorted to check if equal
        for imported_activity, activity in zip(imported_processactivities, original_processactivities):
            imported_activity = imported_activity.dict(by_alias=True, exclude_none=True)
            activity = activity.dict(by_alias=True, exclude_none=True)
            # data needs to be sorted to check if equal
            imported_activity['technosphere_exchanges'].sort(key=lambda x: x['code'], reverse=True)
            imported_activity['biosphere_exchanges'].sort(key=lambda x: x['code'], reverse=True)
            activity['technosphere_exchanges'].sort(key=lambda x: x['code'], reverse=True)
            activity['biosphere_exchanges'].sort(key=lambda x: x['code'], reverse=True)
            if activity != imported_activity:
                for (acitvity_key, acitvity_value), imported_activity_value in zip(activity.items(), imported_activity.values()):
                    # Check if the exchanges match
                    if acitvity_key in ['biosphere_exchanges', 'technosphere_exchanges']:
                        for exchange, imported_exchange in zip(activity[acitvity_key], imported_activity[acitvity_key]):
                            if len(exchange.keys()) != len(imported_exchange.keys()):
                                raise Exception('There are not the same exchange variables in the imported and the original data \n \timported: {}\n\toriginal: {}'.format("; ".join(imported_exchange.keys()), "; ".join(exchange.keys())))
                            for exchange_key in exchange.keys():
                                if exchange[exchange_key] != imported_exchange[exchange_key]:
                                    raise Exception('The following activity could not be recreated correctly {} due to exchange {}. \n \t{}: {} != {}'.format(activity['name'], exchange['name'], exchange_key, exchange[exchange_key], imported_exchange[exchange_key]))
                    # Check if the other activity properties match
                    else:
                        if acitvity_value != imported_activity_value:
                            raise Exception('The following activity could not be recreated correctly {}. \n \t{}: {} != {}'.format(activity['name'], acitvity_key, acitvity_value, imported_activity_value))
        if imported_processactivities != original_processactivities:
            raise Exception('The exported data can not completely be recreated.')

    def check_activities_completeness(self, processactivities: List[ProcessActivityCreate], datasetmetadatacreate: DatasetMetadataCreate, emissionactivities: Optional[List[EmissionActivityCreate]] = []) -> None:
        """
        Performs checks on the completeness of the exported activities.

        Args:
            activities (List[Activity]): A list of Activity objects representing the exported LCI data.
            datasetmetadatacreate (DatasetMetadataCreate): The datasetmetadata object created for the exported LCI database.

        Returns:
            None
        """
        engine_temp, datasetmetadata_temp = self.create_in_memory_sqlite_database(processactivities, datasetmetadatacreate, emissionactivities=emissionactivities)
        temporal_project_name = f"{self.project_name}_for_completeness_check_temporal"
        self.create_temporal_copy_of_current_BW_project(temporal_project_name)
        bw2data.projects.set_current(temporal_project_name)
        # Import the data from the in memory sqlite database
        LCIImporter_temp = LCIImporterSql(temporal_project_name, datasetmetadata_temp.dataset_name, engine_temp)
        LCIImporter_temp.check_matching_of_imported_data()
        # Check if all activities have unique data needed for matching later on
        unique_fields = ['reference product', 'unit', 'location', 'name']
        imported_activities = pd.DataFrame(bw2data.Database(datasetmetadata_temp.dataset_name))
        for duplicate_fields, duplicate_info in imported_activities[imported_activities.duplicated(subset=unique_fields, keep=False)].groupby(unique_fields):
            warnings.warn('duplicates found for {}: \n {}'.format(duplicate_fields, duplicate_info['code'].values))
        # Check if the data "re-extracted" (exported-imported-exported) data and the original data are identical
        imported_activities_reextracted, imported_emssions_acitivities_reextracted = self.extract_lci_data(databases='')
        self._compare_imported_to_original_processactivities(imported_processactivities=imported_activities_reextracted, original_processactivities=processactivities)
        # ATTN: Implement test for imported_emssions_acitivities_reextracted as well.
        # Leave the temporal brightway project directory
        bw2data.project.projects._restore_orig_directory()
        bw2data.projects.set_current(self.project_name)
        print('The data was checked successfuly for completeness')

    def check_background_database_dependency(self) -> List[str]:
        """
        Checks and returns a list of background databases on which the exported databases depend.

        Returns:
            List[str]: A list of background database names on which the exported databases depend.
        """
        background_databases = []
        for db_name in self.databases:
            db = bw2data.Database(db_name)
            background_databases += db.metadata.get("depends", [])
        background_database_dependency = []
        for database in background_databases:
            if (
                database not in self.databases
                and database not in background_database_dependency
            ):
                background_database_dependency.append(database)
        print(
            "The exported database is dependant on: {}".format(
                ", ".join(background_database_dependency)
            )
        )
        return background_database_dependency

    def create_metadata(
        self, 
        dataset_name: str, 
        dataset_final_date: date, 
        description: str,
        user_email_addres: str,
        keywords_input: list = [],
    ) -> DatasetMetadataCreate:
        """
        Creates metadata for the exported data and dataset.

        Args:
            dataset_name (str): The name of the current dataset in the application.
            dataset_final_date (date): The final date of the LCI dataset.
            description (str): A description of the LCI dataset.
            user_email_addres (str): The email address of the user creating the LCI dataset.
            keywords_input (list, optional): A list of keywords associated with the LCI dataset.
                Defaults to [].

        Returns:
            datasetmetadatacreate: The created DatasetMetadataCreate object containing dataset metadata.
        """
        # Create the dependencies
        databasedependancies = []
        for database_name in self.check_background_database_dependency():
            databasedependency = DatabaseDependancyCreate(database_name=database_name)
            databasedependancies.append(databasedependency)
        keywords = []
        for keyword_input in keywords_input:
            keyword = KeywordCreate(name=keyword_input)
            keywords.append(keyword)
        datasetmetadatacreate = DatasetMetadataCreate(
            dataset_name = dataset_name,
            dataset_final_date = dataset_final_date,
            description = description,
            version = self.create_version(dataset_name),
            user_email_addres = user_email_addres
            )
        datasetmetadatacreate.update_forward_refs()
        datasetmetadatacreate.keywords=keywords
        datasetmetadatacreate.databasedependencies=databasedependancies

        return datasetmetadatacreate
    
    def check_datasetmetadata_completeness(self, datasetmetadata:DatasetMetadata):
        if len(self.databases) > 1:
            warnings.warn("There are multiple databases specified to be imported, they will be imported as one database.")
        # TO-DO: Write method
        # Check if there is a dataset with the same name or contains the same name
        
        # Check if the background databases are available databases, either based on a "trusted" list, or with user interaction
        # Suggest that the other background database should also be imported
        return None

    def create_version(self, dataset_name:str) -> float:
        # TO-DO: Implement versioning system
        datasetmetadatalist = self.crud.read_all_datasetmetadata()
        datasetmetadataselection = [datasetmetadata for datasetmetadata in datasetmetadatalist if datasetmetadata.dataset_name == dataset_name]
        if len(datasetmetadataselection) == 0:
            version = 0
        else:
            datasetmetadataselection.sort(key=lambda x: x.version, reverse=True)
            version = datasetmetadataselection[0].version + 1
            warnings.warn('There are multiple version to the dataset with the name: {}, the dataset will be saved with the new version number: {}'.format(dataset_name, version))
        return version
    
    def export_to_sql(self, processactivities: List[ProcessActivityCreate], datasetmetadata: DatasetMetadataCreate, emissionactivities: Optional[List[EmissionActivityCreate]] = []) -> None:
        """
        Exports the metadata and the activity data to the sql database represented by the engine.

        Args:
            processactivities (List[ProcessActivityCreate]): A list of process Activity objects representing the exported LCI data.
            datasetmetadata (DatasetMetadataCreate): The datasetmetadata object created for the exported LCI database.
            emissionactivities (List[EmissionActivityCreate]): A list of emission Activity objects representing the exported LCI data.

        Returns:
            None
        """
        datasetmetadata = self.crud.create_datasetmetadata(datasetmetadatacreate=datasetmetadata)
        self.crud.create_process_activities(activities=processactivities, datasetmetadata_id=datasetmetadata.id)
        self.crud.create_emission_activities(activities=emissionactivities, datasetmetadata_id=datasetmetadata.id)