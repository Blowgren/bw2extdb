from typing import List, Optional
from datetime import date
from sqlmodel import Field, Relationship, SQLModel

# TO-DO:
# - rewrite the Read classes to not include the ID, except for activity_id
# - Change that all exchnages and activities have the same variable name for activity_id
# - Rethink if it makes sense to seperate technosphere and biosphere activities
# - How to deal with emission activities, should we split acitivities in three models: process, emissions and products?

""" Activity base model """
class ActivityBase(SQLModel, allow_population_by_field_name = True):
    id: Optional[int] = Field(default=None, primary_key=True, alias="activity_id")
    code: str
    name: str
    unit: str
    type: str
    comment: Optional[str] # ATTN: should comments be optional???
    database_old: str
    biosphere_version: Optional[str]

""" Process Activity model """
class ProcessActivityBase(ActivityBase):
    location: str
    reference_product: str = Field(alias="reference product")

class ProcessActivity(ProcessActivityBase, table=True):
    datasetmetadata_id: Optional[int] = Field(default=None, foreign_key="datasetmetadata.id")
    technosphere_exchanges: Optional[List["TechnosphereExchange"]] = Relationship()
    biosphere_exchanges: Optional[List["BiosphereExchange"]] = Relationship()

class ProcessActivityCreate(ProcessActivityBase):
    datasetmetadata_id: Optional[int] = Field(default=None, foreign_key="datasetmetadata.id")
    technosphere_exchanges: Optional[List["TechnosphereExchangeCreate"]] = []
    biosphere_exchanges: Optional[List["BiosphereExchangeCreate"]] = []

class ProcessActivityRead(ProcessActivityBase):
    technosphere_exchanges: Optional[List["TechnosphereExchangeRead"]] = []
    biosphere_exchanges: Optional[List["BiosphereExchangeRead"]] = []

""" Emission Activity model """
class EmissionActivityBase(ActivityBase):
    location: Optional[str]

class EmissionActivity(EmissionActivityBase, table=True):
    datasetmetadata_id: Optional[int] = Field(default=None, foreign_key="datasetmetadata.id")
    categories: Optional[List["Category"]] = Relationship()

class EmissionActivityCreate(EmissionActivityBase):
    datasetmetadata_id: Optional[int] = Field(default=None, foreign_key="datasetmetadata.id")
    categories: Optional[List["CategoryCreate"]] = []

class EmissionActivityRead(EmissionActivityBase):
    categories: Optional[List["CategoryRead"]] = []

""" Exchange base model """
class ExchangeBase(SQLModel, allow_population_by_field_name = True):
    id: Optional[int] = Field(default=None, primary_key=True)
    activity_id: Optional[int] = Field(default=None, foreign_key="processactivity.id")
    output_code: str
    name: str
    amount: float
    type: str
    unit: str
    input_code: str = Field(alias="code")
    uncertainty_type: Optional[str] = Field(alias="uncertainty type")
    loc: Optional[float] 
    scale: Optional[float] 
    minimum: Optional[float] 
    maximum: Optional[float]

""" TechnosphereExchange models """
class TechnosphereExchangeBase(ExchangeBase, allow_population_by_field_name = True):
    formula: Optional[str]
    location: str
    reference_product: str = Field(alias="reference product")

class TechnosphereExchange(TechnosphereExchangeBase, table=True):
    categories: Optional[List["Category"]] = Relationship()

class TechnosphereExchangeCreate(TechnosphereExchangeBase):
    categories: Optional[List["CategoryCreate"]] = []
    activity: Optional[ProcessActivityCreate]

class TechnosphereExchangeRead(TechnosphereExchangeBase):
    categories: Optional[List["CategoryRead"]] = []
    input_code: str = Field(alias="code")

""" BiosphereExchamge models"""
class BiosphereExchangeBase(ExchangeBase):
    location: Optional[str]

class BiosphereExchange(BiosphereExchangeBase, table=True):
    categories: Optional[List["Category"]] = Relationship()

class BiosphereExchangeCreate(BiosphereExchangeBase):
    categories: Optional[List["CategoryCreate"]] = []
    activity: Optional[ProcessActivityCreate]

class BiosphereExchangeRead(BiosphereExchangeBase):
    categories: Optional[List["CategoryRead"]] = []

""" Category models """
class CategoryBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    technosphereexchange_id: Optional[int] = Field(default=None, foreign_key="technosphereexchange.id")
    biosphereexchange_id: Optional[int] = Field(default=None, foreign_key="biosphereexchange.id")
    emissionacitivity_id: Optional[int] = Field(default=None, foreign_key="emissionactivity.id")

class Category(CategoryBase, table=True):
    pass
    # technosphere_exchanges: Optional[TechnosphereExchange] = Relationship(back_populates="categories")
    # biosphere_exchanges: Optional[BiosphereExchange] = Relationship(back_populates="categories")

class CategoryCreate(CategoryBase):
    pass
    # technosphere_exchanges: Optional[TechnosphereExchangeCreate] = []
    # biosphere_exchanges: Optional[BiosphereExchangeCreate] = []

class CategoryRead(CategoryBase):
    pass

""" Databasedependancy models """
class DatabaseDependancyBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    database_name: str
    datasetmetadata_id: Optional[int] = Field(default=None, foreign_key="datasetmetadata.id")

class DatabaseDependancy(DatabaseDependancyBase, table=True):
    datasetmetadata: "DatasetMetadata" = Relationship(back_populates="databasedependencies")

class DatabaseDependancyCreate(DatabaseDependancyBase):
    datasetmetadata: Optional["DatasetMetadataCreate"]

class DatabaseDependancyRead(DatabaseDependancyBase):
    pass

""" DatasetMetadata models """
class DatasetMetadataBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_name: str
    dataset_final_date: date
    description: str
    version: float
    user_email_addres: str
    
class DatasetMetadata(DatasetMetadataBase, table=True):
    keywords: List["Keyword"] = Relationship(back_populates="DatasetMetadata")
    databasedependencies: List[DatabaseDependancy] = Relationship(back_populates="datasetmetadata")

class DatasetMetadataCreate(DatasetMetadataBase):
    keywords: Optional[List["KeywordCreate"]] = []
    databasedependencies: Optional[List[DatabaseDependancyCreate]] = []

class DatasetMetadataRead(DatasetMetadataBase):
    keywords: Optional[List["KeywordRead"]] = []
    databasedependencies: Optional[List[DatabaseDependancyRead]] = []

""" Keyword models """
class KeywordBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    datasetmetadata_id: Optional[int] = Field(default=None, foreign_key="datasetmetadata.id")

class Keyword(KeywordBase, table=True):
    DatasetMetadata: "DatasetMetadata" = Relationship(back_populates="keywords")

class KeywordCreate(KeywordBase):
    DatasetMetadata: Optional["DatasetMetadataCreate"]

class KeywordRead(KeywordBase):
    pass

""" Parameter models """
class Parameters(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    type: str
    value: float