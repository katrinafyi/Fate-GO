from fgo_tools import *
from fgo_tools_experimental import SummerProjectsOptimiser2
import pytest
import os
import json

@pytest.fixture
def drops_data():
    return DropsData({
        'location 1': {
            'mat 1': {
                'initial': 1.5,
                'stacks': 100
            }
        }
    })

class TestDropsData:
    def test_stacks(self, drops_data: DropsData):
        assert drops_data.stacks('location 1') == Items({'mat 1': 100})

    def test_drops(self, drops_data: DropsData):
        assert drops_data.drops_with_bonus('location 1', Items({
            'mat 1': 10
        })) == Items({'mat 1': 1001.5})


def _project(name, **materials):
    return {
        'name': name,
        'cost': materials
    }

@pytest.fixture
def project_optimiser():
    s = SummerProjectsOptimiser(False)
    s.set_farming_nodes({
        'farming node 1': {'mat1': 100},
        'farming node 2': {
            'mat2': 200,
            'mat1': 100,
        }
    })
    s.set_projects([
        [
            _project('Project 1 A', mat1=2000),
            _project('Project 1 B', mat2=3500)
        ],
        [
            _project('Project 2 A', mat1=1000),
            _project('Project 2 B', mat2=800)
        ]
    ])
    return s

@pytest.fixture
def proj_opt_2():
    opt = SummerProjectsOptimiser2(False)
    opt.set_projects([
        [
            _project('Project 1 A', mat1=2000),
            _project('Project 1 B', mat2=3500),
            _project('Project 1 C', mat2=3500),
            _project('Project 1 D', mat2=3500),
        ],
        [
            _project('Project 2 A', mat1=1000),
            _project('Project 2 B', mat2=800)
        ]
    ])
    opt.set_farming_nodes({
        'farming node 1': {'mat1': 100},
        'farming node 2': {
            'mat2': 200,
            'mat1': 100,
        }
    })
    return opt

class TestProjOpt2:

    def test_optimiser_2(self):
        os.chdir(os.path.dirname(__file__) + '/2018_07_summer')
    
        with open('part_2_drops.json', encoding='utf-8') as f:
            raw_data = json.decoder.JSONDecoder().decode(f.read())
        data = DropsData(raw_data)

        with open('part_2_projects.json', encoding='utf-8') as f:
            project_data = json.decoder.JSONDecoder().decode(f.read())
            
        my_servants = [
            Items(blue=1), 
            Items(gold=1),
            Items(silver=1),
            Items(oil=1),
            Items(cement=1)
        ]*5
        my_ces = []
        available_supports = [
            Items(blue=1), 
            Items(gold=1),
            Items(silver=1),
            Items(oil=1),
            Items(cement=1)
        ]
        
        available = PartySetup(my_servants, my_ces, available_supports)

        optimiser = SummerProjectsOptimiser2(chunked=True)
        
        farming_nodes_1 = data.optimise_drops(
            ['underworld advanced', 'fields advanced', 'coast advanced', 'cave advanced'],
            available
        )

        farming_nodes_2 = data.optimise_drops(['underworld explosion', 
            'fields explosion', 'coast explosion', 'cave explosion',
            'city explosion'], available)
        farming_nodes_2['contaminated explosion'] = data.drops_with_bonus(
            'contaminated explosion', Items(silver=2, gold=2, blue=2)
        )

        optimiser.set_projects([
            project_data[:5],
            project_data[5:]
        ])
        optimiser.set_farming_nodes([farming_nodes_1, farming_nodes_2])
        output = optimiser.optimise_projects()
        print(json.encoder.JSONEncoder(indent=2).encode(output))
        assert output[0]['total_runs'] + output[1]['total_runs'] == 25

