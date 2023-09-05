from typing import List, Union
from sqlmodel import Session, select

from .models import *

class Crud():

    def __init__(self, engine) -> None:
        self.engine = engine

    def create_process_activities(self, activities: List[ProcessActivityCreate], projectmetadata_id:int) -> None:
        """
        Creates activities and their related biosphere and technosphere exchanges in the database.

        Parameters:
            activities (List[ProcessActivityCreate]): A list of ProcessActivityCreate objects representing the activities to be created.
            projectmetadata_id (int): The ID of the ProjectMetadata associated with the activities.

        Returns:
            None
        """
        with Session(self.engine) as session:
            for activity_data in activities:
                activity = ProcessActivity.from_orm(activity_data)
                activity.projectmetadata_id = projectmetadata_id
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

    def create_emission_activities(self, activities: List[EmissionActivityCreate], projectmetadata_id:int) -> None:
        """
        Creates emission activities in the database.

        Parameters:
            activities (List[EmissionActivityCreate]): A list of EmissionActivityCreate objects representing the activities to be created.
            projectmetadata_id (int): The ID of the ProjectMetadata associated with the activities.

        Returns:
            None
        """
        with Session(self.engine) as session:
            for activity_data in activities:
                activity = EmissionActivity.from_orm(activity_data)
                activity.projectmetadata_id = projectmetadata_id
                session.add(activity)
                session.commit()
            # return activities
        
    def create_projectmetadata(self, projectmetadatacreate: ProjectMetadataCreate) -> None:
        """
        Creates a ProjectMetadata object in the database.

        Parameters:
            projectmetadatacreate (ProjectMetadataCreate): The ProjectMetadataCreate object representing the project metadata.

        Returns:
            ProjectMetadata: The created ProjectMetadata object.
        """
        with Session(self.engine) as session:
            projectmetadata = ProjectMetadata.from_orm(projectmetadatacreate)
            session.add(projectmetadata)
            session.commit()
            session.refresh(projectmetadata)
            if projectmetadatacreate.databasedependencies:
                for databasedependency_data in projectmetadatacreate.databasedependencies:
                    databasedependency_data.projectmetadata_id = projectmetadata.id
                    databasedependency = DatabaseDependancy.from_orm(databasedependency_data)
                    session.add(databasedependency)
            if projectmetadatacreate.keywords:
                for keyword_data in projectmetadatacreate.keywords:
                    keyword_data.projectmetadata_id = projectmetadata.id
                    keyword = Keyword.from_orm(keyword_data)
                    session.add(keyword)
            session.commit()
            session.refresh(projectmetadata)
            return projectmetadata

    def read_projectmetadata(self, projectmetadata_key: Union[int, str]) -> ProjectMetadataRead:
        """
        Retrieves the ProjectMetadataRead object from the database based on the provided key.

        Parameters:
            projectmetadata_key (Union[int, str]): The ID or name of the ProjectMetadata to be retrieved.

        Returns:
            ProjectMetadataRead: The retrieved ProjectMetadataRead object.
        """
        with Session(self.engine) as session:
            if isinstance(projectmetadata_key, str):
                statement = select(ProjectMetadata).where(ProjectMetadata.project_name == projectmetadata_key)
                results = session.exec(statement)
                projectmetadata = results.one()
            else:
                projectmetadata = session.get(ProjectMetadata, projectmetadata_key)
                if not projectmetadata:
                    raise Exception(f"No projectmetadata to the key {projectmetadata_key}")
            ProjectMetadataRead.update_forward_refs()
            projectmetadata_output = ProjectMetadataRead.from_orm(projectmetadata)
            return projectmetadata_output
        
        
    def read_process_activities(self, projectmetadata_key:int) -> List[ProcessActivityRead]:
        """
        Retrieves a list of ProcessActivityRead objects associated with the given ProjectMetadata ID.

        Parameters:
            projectmetadata_key (int): The ID of the ProjectMetadata.

        Returns:
            List[ProcessActivityRead]: A list of retrieved ProcessActivityRead objects.
        """
        with Session(self.engine) as session:
            statement = select(ProcessActivity).where(ProcessActivity.projectmetadata_id == projectmetadata_key)
            results = session.exec(statement)
            activities = results.all()
            ProcessActivityRead.update_forward_refs()
            TechnosphereExchangeRead.update_forward_refs()
            BiosphereExchangeRead.update_forward_refs()
            activities_output = []
            for activity in activities:
                activities_output.append(ProcessActivityRead.from_orm(activity))
        return activities_output
    
    def read_emission_activities(self, projectmetadata_key:int) -> List[EmissionActivityRead]:
        """
        Retrieves a list of EmissionActivityRead objects associated with the given ProjectMetadata ID.

        Parameters:
            projectmetadata_key (int): The ID of the ProjectMetadata.

        Returns:
            List[EmissionActivityRead]: A list of retrieved EmissionActivityRead objects.
        """
        with Session(self.engine) as session:
            statement = select(EmissionActivity).where(EmissionActivity.projectmetadata_id == projectmetadata_key)
            results = session.exec(statement)
            activities = results.all()
            EmissionActivityRead.update_forward_refs()
            activities_output = []
            for activity in activities:
                activities_output.append(EmissionActivityRead.from_orm(activity))
        return activities_output

    def read_all_projectmetadata(self) -> List[ProjectMetadataRead]:
        """
        Retrieves the ProjectMetadataRead object from the database based on the provided key.

        Returns:
            List[ProjectMetadataRead]: The retrieved ProjectMetadataRead objects.
        """
        with Session(self.engine) as session:
            statement = select(ProjectMetadata)
            results = session.exec(statement)
            projectmetadatas = results.all()
            ProjectMetadataRead.update_forward_refs()
            projectmetadata_output = [ProjectMetadataRead.from_orm(projectmetadata) for projectmetadata in projectmetadatas]
            return projectmetadata_output   
    # app = FastAPI()
    # @app.get("/activities/", response_model=List[ActivityRead])
    # def read_heroes():
    #     with Session(self.engine) as session:
    #         activities = session.exec(select(Activity)).all()
    #         return activities