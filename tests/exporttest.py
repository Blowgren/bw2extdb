import pytest
import bw2data
from bw2extdb.exportImport.exporter import LCIExporter
from bw2extdb.exportImport.models import Activity, Exchange

# TO-DO:
# - figure out how an attribute is not created when None is passed (for Activity and Exchange)
# - Does it make sense to test the variable input types to avoid mistakes, will this really be relevant?

def test_check_background_database_dependency():
    # TODO: Implement
    assert True == False

def test_create_metadata():
    # TODO: Implement
    assert True == False

def test_extract_lci_data__activities(setup):
    # Setup and initialize the extractor using the setup-method
    project_name = "default"
    databases = ['example']
    LCIExporter_test = LCIExporter(project_name, databases)
    activities, _ = LCIExporter_test.extract_lci_data()
    # Define the expected list of Activity and Exchange objects
    expected_activities = [
        Activity(
            code="9c8761035420f7fa83dc9244b4b54948", #ATTN: alt. use the activity_hash method
            location="loc1", 
            name="name1", 
            reference_product="ref_prod1", 
            unit="unit1", 
            act_type="type1", 
            comment="comment1", 
            biosphere_version="0.8.8"
        ),
        Activity(
            code="3a566dc307f700be307d1dc84f864968", 
            location="loc2", 
            name="name2", 
            reference_product="ref_prod2", 
            unit="unit2",
            act_type="type2", 
            comment="comment2", 
            biosphere_version="0.8.8"
        ),
        # Add more expected Activity objects as needed
    ]

    # Perform assertions to verify the extracted data
    assert len(activities) == len(expected_activities)
    # Sort the lists of activities based on the name to compare the correct exactivities
    activity.sort(key=lambda x: x.name)
    expected_activity.sort(key=lambda x: x.name)
    for activity, expected_activity in zip(activities, expected_activities):
        assert isinstance(activity, Activity)
        assert activity.code == expected_activity.code
        assert activity.location == expected_activity.location
        assert activity.name == expected_activity.name
        assert activity.reference_product == expected_activity.reference_product
        assert activity.unit == expected_activity.unit
        assert activity.type == expected_activity.type
        assert activity.comment == expected_activity.comment
        assert activity.biosphere_version == expected_activity.biosphere_version

def test_extract_lci_data__exchanges(setup):
    # Setup and initialize the extractor using the setup-method
    project_name = "default"
    databases = ['example']
    LCIExporter_test = LCIExporter(project_name, databases)
    _, exchanges = LCIExporter_test.extract_lci_data()
    expected_exchanges = [
        Exchange(
            output_code="9c8761035420f7fa83dc9244b4b54948", 
            location="loc1", 
            unit="unit1", 
            categories=None, 
            name="name1", 
            input_code="9c8761035420f7fa83dc9244b4b54948", 
            reference_product="ref_prod1", 
            amount=0.5, 
            ex_type="production", 
            formula=None
        ),
        Exchange(
            output_code="3a566dc307f700be307d1dc84f864968", 
            location="loc2", 
            unit="unit2", 
            categories=["cat21", "cat22"], 
            name="name2", 
            input_code="3a566dc307f700be307d1dc84f864968", 
            reference_product="ref_prod2",
            amount=10, 
            ex_type="production", 
            formula=None
        ),
        Exchange(
            output_code="3a566dc307f700be307d1dc84f864968", 
            location="loc1", 
            unit="unit1", 
            categories=None, 
            name="name1", 
            input_code="9c8761035420f7fa83dc9244b4b54948", 
            reference_product="ref_prod1",
            amount=100.1, 
            ex_type="technosphere", 
            formula="foo * bar + 4"
        ),
        # Add more expected Exchange objects as needed
    ]
    # Sort the lists of exchnages based on the amount to compare the correct exchanges
    exchanges.sort(key=lambda x: x.amount)
    expected_exchanges.sort(key=lambda x: x.amount)
    assert len(exchanges) == len(expected_exchanges)
    for exchange, expected_exchange in zip(exchanges, expected_exchanges):
        assert isinstance(exchange, Exchange)
        assert exchange.output_code == expected_exchange.output_code
        assert exchange.location == expected_exchange.location
        assert exchange.unit == expected_exchange.unit
        assert exchange.categories == expected_exchange.categories
        assert exchange.name == expected_exchange.name
        assert exchange.code == expected_exchange.code
        assert exchange.reference_product == expected_exchange.reference_product
        assert exchange.amount == expected_exchange.amount
        assert exchange.type == expected_exchange.type
        assert exchange.formula == expected_exchange.formula