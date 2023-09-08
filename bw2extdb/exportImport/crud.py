from typing import List, Union
from sqlmodel import Session, select

from .models import *

class Crud():

    def __init__(self, engine) -> None:
        self.engine = engine

    def create_process_activities(self, activities: List[ProcessActivityCreate], datasetmetadata_id:int) -> None:
        """
        Creates activities and their related biosphere and technosphere exchanges in the database.

        Parameters:
            activities (List[ProcessActivityCreate]): A list of ProcessActivityCreate objects representing the activities to be created.
            datasetmetadata_id (int): The ID of the DatasetMetadata associated with the activities.

        Returns:
            None
        """
        # ATTN: This method should only have one commit, by using relationships in the database models
        with Session(self.engine) as session:
            for activity_data in activities:
                activity = ProcessActivity.from_orm(activity_data)
                activity.datasetmetadata_id = datasetmetadata_id
                session.add(activity)
                session.commit()
                session.refresh(activity)
                if activity_data.biosphere_exchanges:
                    for biosphere_exchange_data in activity_data.biosphere_exchanges:
                        biosphere_exchange_data.activity_id = activity.id
                        biosphere_exchange = BiosphereExchange.from_orm(biosphere_exchange_data)
                        session.add(biosphere_exchange)
                        session.commit()
                        session.refresh(biosphere_exchange)
                        if biosphere_exchange_data.categories:
                            for category_data in biosphere_exchange_data.categories:
                                category_data.biosphereexchange_id = biosphere_exchange.id
                                category = Category.from_orm(category_data)
                                session.add(category)
                if activity_data.technosphere_exchanges:
                    for technosphere_exchange_data in activity_data.technosphere_exchanges:
                        technosphere_exchange_data.activity_id = activity.id
                        technosphere_exchange = TechnosphereExchange.from_orm(technosphere_exchange_data)
                        session.add(technosphere_exchange)
                        session.commit()
                        session.refresh(technosphere_exchange)
                        if technosphere_exchange_data.categories:
                            for category_data in technosphere_exchange_data.categories:
                                category_data.technosphereexchange_id = technosphere_exchange.id
                                category = Category.from_orm(category_data)
                                session.add(category)
                session.commit()
            # return activities

    def create_emission_activities(self, activities: List[EmissionActivityCreate], datasetmetadata_id:int) -> None:
        """
        Creates emission activities in the database.

        Parameters:
            activities (List[EmissionActivityCreate]): A list of EmissionActivityCreate objects representing the activities to be created.
            datasetmetadata_id (int): The ID of the DatasetMetadata associated with the activities.

        Returns:
            None
        """
        with Session(self.engine) as session:
            for activity_data in activities:
                activity = EmissionActivity.from_orm(activity_data)
                activity.datasetmetadata_id = datasetmetadata_id
                session.add(activity)
                session.commit()
            # return activities
        
    def create_datasetmetadata(self, datasetmetadatacreate: DatasetMetadataCreate) -> None:
        """
        Creates a DatasetMetadata object in the database.

        Parameters:
            datasetmetadatacreate (DatasetMetadataCreate): The DatasetMetadataCreate object representing the dataset metadata.

        Returns:
            DatasetMetadata: The created DatasetMetadata object.
        """
        with Session(self.engine) as session:
            datasetmetadata = DatasetMetadata.from_orm(datasetmetadatacreate)
            session.add(datasetmetadata)
            session.commit()
            session.refresh(datasetmetadata)
            if datasetmetadatacreate.databasedependencies:
                for databasedependency_data in datasetmetadatacreate.databasedependencies:
                    databasedependency_data.datasetmetadata_id = datasetmetadata.id
                    databasedependency = DatabaseDependancy.from_orm(databasedependency_data)
                    session.add(databasedependency)
            if datasetmetadatacreate.keywords:
                for keyword_data in datasetmetadatacreate.keywords:
                    keyword_data.datasetmetadata_id = datasetmetadata.id
                    keyword = Keyword.from_orm(keyword_data)
                    session.add(keyword)
            session.commit()
            session.refresh(datasetmetadata)
            return datasetmetadata

    def read_datasetmetadata(self, datasetmetadata_key: Union[int, str]) -> DatasetMetadataRead:
        """
        Retrieves the DatasetMetadataRead object from the database based on the provided key.

        Parameters:
            datasetmetadata_key (Union[int, str]): The ID or name of the DatasetMetadata to be retrieved.

        Returns:
            DatasetMetadataRead: The retrieved DatasetMetadataRead object.
        """
        with Session(self.engine) as session:
            if isinstance(datasetmetadata_key, str):
                statement = select(DatasetMetadata).where(DatasetMetadata.dataset_name == datasetmetadata_key)
                results = session.exec(statement)
                datasetmetadata = results.one()
            else:
                datasetmetadata = session.get(DatasetMetadata, datasetmetadata_key)
                if not datasetmetadata:
                    raise Exception(f"No datasetmetadata to the key {datasetmetadata_key}")
            DatasetMetadataRead.update_forward_refs()
            datasetmetadata_output = DatasetMetadataRead.from_orm(datasetmetadata)
            return datasetmetadata_output
        
        
    def read_process_activities(self, datasetmetadata_key:int) -> List[ProcessActivityRead]:
        """
        Retrieves a list of ProcessActivityRead objects associated with the given DatasetMetadata ID.

        Parameters:
            datasetmetadata_key (int): The ID of the DatasetMetadata.

        Returns:
            List[ProcessActivityRead]: A list of retrieved ProcessActivityRead objects.
        """
        with Session(self.engine) as session:
            statement = select(ProcessActivity).where(ProcessActivity.datasetmetadata_id == datasetmetadata_key)
            results = session.exec(statement)
            activities = results.all()
            ProcessActivityRead.update_forward_refs()
            TechnosphereExchangeRead.update_forward_refs()
            BiosphereExchangeRead.update_forward_refs()
            activities_output = []
            for activity in activities:
                activities_output.append(ProcessActivityRead.from_orm(activity))
        return activities_output
    
    def read_emission_activities(self, datasetmetadata_key:int) -> List[EmissionActivityRead]:
        """
        Retrieves a list of EmissionActivityRead objects associated with the given DatasetMetadata ID.

        Parameters:
            datasetmetadata_key (int): The ID of the DatasetMetadata.

        Returns:
            List[EmissionActivityRead]: A list of retrieved EmissionActivityRead objects.
        """
        with Session(self.engine) as session:
            statement = select(EmissionActivity).where(EmissionActivity.datasetmetadata_id == datasetmetadata_key)
            results = session.exec(statement)
            activities = results.all()
            EmissionActivityRead.update_forward_refs()
            activities_output = []
            for activity in activities:
                activities_output.append(EmissionActivityRead.from_orm(activity))
        return activities_output

    def read_all_datasetmetadata(self) -> List[DatasetMetadataRead]:
        """
        Retrieves the DatasetMetadataRead object from the database based on the provided key.

        Returns:
            List[DatasetMetadataRead]: The retrieved DatasetMetadataRead objects.
        """
        with Session(self.engine) as session:
            statement = select(DatasetMetadata)
            results = session.exec(statement)
            datasetmetadatas = results.all()
            DatasetMetadataRead.update_forward_refs()
            datasetmetadata_output = [DatasetMetadataRead.from_orm(datasetmetadata) for datasetmetadata in datasetmetadatas]
            return datasetmetadata_output   
    # app = FastAPI()
    # @app.get("/activities/", response_model=List[ActivityRead])
    # def read_heroes():
    #     with Session(self.engine) as session:
    #         activities = session.exec(select(Activity)).all()
    #         return activities