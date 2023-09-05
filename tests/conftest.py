import pytest
from bw2io.strategies.generic import set_code_by_activity_hash
from bw2data.tests import bw2test
from bw2data import Database
from bw2data.parameters import parameters, ActivityParameter, ParameterizedExchange, DatabaseParameter, ProjectParameter, projects

@pytest.fixture
@bw2test
def setup():
    db = Database("example")
    db.register(extra="yes please")
    data = {
        ("example","code1"):{
            "code":"code1",
            "location":"loc1", 
            "name":"name1", 
            "unit":"unit1", 
            "comment":"comment1", 
            "reference product":"ref_prod1",
            "type":"type1",
            "exchanges":[
                {
                    "amount": 0.5,
                    "input": ("example", "code1"),
                    "type": "production",
                },
            ]
        },
        ("example","code2"):{
            "code":"code2",
            "location":"loc2", 
            "name":"name2", 
            "unit":"unit2", 
            "comment":"comment2", 
            "reference product":"ref_prod2",
            "type":"type2",
            "categories":["cat21", "cat22"],
            "exchanges":[
                {
                    "amount": 10,
                    "input": ("example", "code2"),
                    "type": "production",
                },
                {
                    "amount": 100.1,
                    "input": ("example", "code1"),
                    "type": "technosphere",
                    "formula": "foo * bar + 4",
                }
            ]
        },
    }
    db.write(data)
    set_code_by_activity_hash(db=db, overwrite=True)