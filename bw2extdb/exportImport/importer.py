from typing import List, Tuple, Dict, Any, Union
import collections
from sqlalchemy.engine.base import Engine
import warnings

import bw2data
from bw2io.importers.base_lci import LCIImporter
from bw2io.utils import activity_hash


from .crud import Crud

class LCIImporterSql(LCIImporter):
    """
    Import Life Cycle Inventory (LCI) data from an SQLite database into the current application.

    This class allows importing LCI data, activities, exchanges, and related metadata from an SQLite database
    into the current application. It is a subclass of `bw2io.importers.base_lci.LCIImporter` and inherits its methods.

    Args:
        project_name (str): The name of the current project in the application.
        dataset_name (str): The name of the project's database.
        engine (Engine): The sqlalchemy or sqlmodel engine object linking to the sql database

    Attributes:
        project_name (str): The name of the current project in the application.
        dataset_name (str): The name of the dataset's database.
        crud (obj): The create-read-update-delete object for the sql-database
        db_name (str): The name of the database from the project metadata.
        metadata (dict): The dataset metadata.

    Methods:
        get_datasetmetadata_id(self, dataset_name: str) -> int:
            Get the metadata ID of the dataset from the specified dataset name.

        process_activities(self, datasetmetadata_id: int) -> List[dict]:
            Process the activities and their exchanges from the specified dataset metadata ID.

        get_database(self, datasetmetadata_id: int) -> Tuple[str, dict]:
            Get the name and metadata of the database from the specified dataset metadata ID.

        get_database_dependencies(self, datasetmetadata_id: int) -> List[str]:
            Get a list of background databases on which the specified dataset metadata depends.

        get_project_parameters(self) -> None:
            Get project-specific parameters. TO-DO: Implement this method.

        get_database_parameters(self) -> None:
            Get database-specific parameters. TO-DO: Implement this method.

        check_imported_data(self) -> None:
            Check the integrity and correctness of the imported data.

        link_imported_database(self) -> bool:
            Link the imported database by matching fields and checking statistics.

    Examples:
        # Initialize the LCIImporterSql
        importer_sql = LCIImporterSql(project_name="MyLCIProject", dataset_name="MyLCIDatabase", sql_database="path/to/database.db")

        # Check imported data
        importer_sql.check_imported_data()

        # Link the imported database
        importer_sql.link_imported_database()
    """

    def __init__(
        self, project_name: str, dataset_name: str, engine: Engine
    ):
        # This class is structural copy from bw2io.importers.excel.ExcelImporter
        # https://github.com/brightway-lca/brightway2-io/blob/f2f5f57f437a6a9bbe584a428f6cca3100edceb2/bw2io/importers/excel.py
        self.project_name = project_name
        self.dataset_name = dataset_name
        self.crud = Crud(engine)
        bw2data.projects.set_current(project_name)
        datasetmetadata_id = self.get_datasetmetadata_id(dataset_name)
        self.db_name, self.metadata = self.get_database(datasetmetadata_id)
        self.project_parameters = self.get_project_parameters()
        self.database_parameters = self.get_database_parameters()
        self.data = self.process_activities(datasetmetadata_id)
        self.database_dependencies = self.get_database_dependencies(datasetmetadata_id)

    def get_datasetmetadata_id(self, dataset_name: str) -> int:
        """
        Get the metadata ID of the dataset from the specified dataset name.

        Args:
            dataset_name (str): The name of the current dataset in the application.

        Returns:
            int: The metadata ID of the dataset.
        """
        datasetmetadatalist = self.crud.read_all_datasetmetadata()
        datasetmetadataselection = [datasetmetadata for datasetmetadata in datasetmetadatalist if datasetmetadata.dataset_name == dataset_name]
        if len(datasetmetadataselection) == 0:
            raise Exception(f"No datasetmetadata to the name: {dataset_name}") 
        elif len(datasetmetadataselection) == 1:
            return datasetmetadataselection[0].id
        else:
            datasetmetadataselection.sort(key=lambda x: x.version, reverse=True)
            latest_version = datasetmetadataselection[0].version
            datasetmetadatasubselection = [datasetmetadata for datasetmetadata in datasetmetadatalist if datasetmetadata.version == latest_version]
            if len(datasetmetadatasubselection) > 1:
                raise Exception(f"There are multiple versions to the dataset: {dataset_name}")
            else:
                warnings.warn('There are multiple version to the dataset with the name: {}, the latest version is chosen (version: {})'.format(dataset_name, datasetmetadataselection[0].version))
                return datasetmetadataselection[0].id
            
    def process_activities(self, datasetmetadata_id: int) -> list[dict]:
        """
        Process the activities and their exchanges from the specified dataset metadata ID.

        Args:
            datasetmetadata_id (int): The metadata ID of the dataset.

        Returns:
            List[dict]: A list of dictionaries representing processed activities.
        """
        processactivities = self.crud.read_process_activities(datasetmetadata_key=datasetmetadata_id)
        activities_dicts = []
        for process_activity_raw in processactivities:
            processactivity = process_activity_raw.dict(by_alias=True, exclude_none=True)
            processactivity["exchanges"] = processactivity["biosphere_exchanges"] + processactivity["technosphere_exchanges"]
            processactivity.pop("biosphere_exchanges")
            processactivity.pop("technosphere_exchanges")
            processactivity["database"] = self.dataset_name
            for exchange in processactivity["exchanges"]:
                if exchange["categories"]:
                    exchange["categories"] = [category["name"] for category in exchange["categories"]]
            activities_dicts.append(processactivity)
        emissionactivities = self.crud.read_emission_activities(datasetmetadata_key=datasetmetadata_id)
        for emission_activity_raw in emissionactivities:
            emissionactivity = emission_activity_raw.dict(by_alias=True, exclude_none=True)
            emissionactivity["database"] = self.dataset_name
            if emissionactivity["categories"]:
                emissionactivity["categories"] = [category["name"] for category in emissionactivity["categories"]]
            activities_dicts.append(emissionactivity)
        return activities_dicts

    def get_database(self, datasetmetadata_id: int) -> tuple[str, dict]:
        """
        Get the name and metadata of the database from the specified dataset metadata ID.

        Args:
            datasetmetadata_id (int): The metadata ID of the dataset.

        Returns:
            Tuple[str, dict]: A tuple containing the name and metadata of the database.
        """
        datasetmetadata = self.crud.read_datasetmetadata(datasetmetadata_key=datasetmetadata_id)
        metadata = datasetmetadata.dict(by_alias=True, exclude_none=True)
        # ATTN: JSON is not serilizable with datetime so the datetime needs to be stored as a string, maybe a more generic solution possible?
        metadata["dataset_final_date"] = str(metadata["dataset_final_date"])
        return datasetmetadata.dataset_name, metadata

    def get_database_dependencies(self, datasetmetadata_id: int) -> list[str]:
        """
        Get a list of background databases on which the specified dataset metadata depends.

        Args:
            datasetmetadata_id (int): The metadata ID of the dataset.

        Returns:
            List[str]: A list of background database names on which the dataset depends.
        """
        datasetmetadata = self.crud.read_datasetmetadata(datasetmetadata_key=datasetmetadata_id).dict(by_alias=True, exclude_none=True)
        databasedependencies = [databasedependency['database_name'] for databasedependency in datasetmetadata['databasedependencies']]
        print('The imported dataset is dependent on: \n{}'.format('\n\t'.join(databasedependencies)))
        return databasedependencies

    def get_project_parameters(self):
        # TO-DO: Write method
        # info: https://github.com/brightway-lca/brightway2/blob/master/notebooks/Parameters%20-%20manual%20creation.ipynb
        # info: https://github.com/brightway-lca/brightway2/blob/master/notebooks/Parameters%20-%20Excel%20import.ipynb
        return None

    def get_database_parameters(self):
        # TO-DO: Write method
        return None
    
    def check_imported_data(self):
        # TO-DO: Write method
        # Check if the database dependencies are in the project, else raise Warning/Error
        # Check if the database which is imported already exists
        # Check if linking is correct, by checking the field names
        # Check if the biosphere version checks
        return None

    def check_matching_of_imported_data(self):
        self.match_database(kind="production", fields=["code"])
        # Check if all production flows have an internal match
        if "production" in self._matching_statistics().keys():
            raise Exception('The exported data could not be recreated, {} production exchanges could not be matched'.format(self._matching_statistics()['production']))
        self.match_database(kind="technosphere", fields=["code"])
        for database_dependency in self.database_dependencies:
            if database_dependency is not 'biosphere3':
                self.match_database(database_dependency, fields=['reference product', 'unit', 'location', 'name'], kind='technosphere')
        # ATTN: The internal matching for biosphere is based on an single example and is NOT A GOOD GENERALIZATION, but code deos not work since the biosphere input code is not database+code as for the technosphere
        self.match_database(fields=["name"], kind="biosphere") # Match to biosphere activities in the imported database
        self.match_database("biosphere3", fields=["code"], kind="biosphere")
        if "biosphere" in self._matching_statistics().keys():
            raise Exception('The exported data could not be recreated, {} biosphere exchanges could not be matched'.format(self._matching_statistics()['biosphere']))
        # Check if all remaining technosphere exchanges can be matched to the other databases in the project and write the fully matched data
        if self.statistics()[2] == 0:
            self.write_database()
        else:
            raise Exception("There are technosphere exchanges which remain unlinked, the exported data could not be recreated")
        
    def _matching_statistics(self) -> Dict[str, int]:
        unique_unlinked = collections.defaultdict(set)
        for ds in self.data:
            for exc in (e for e in ds.get("exchanges", []) if not e.get("input")):
                unique_unlinked[exc.get("type")].add(activity_hash(exc))
        unique_unlinked = {k: len(v) for k, v in list(unique_unlinked.items())}
        return unique_unlinked