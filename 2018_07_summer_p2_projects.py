from fgo_tools import *
from fgo_tools import _json
from fgo_tools_experimental import SummerProjectsOptimiser2


import os
import json
import math
from collections import OrderedDict, defaultdict

def _main():
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
    
    for chunk in output:
        if chunk is None: continue
        chunk['projects'] = ', '.join(chunk['projects'])
        chunk['required_materials'] = chunk['required_materials'].friendly_name()

    with open('optimised_part_2_projects.json', 'w') as f:
        f.write(_json(output))


if __name__ == '__main__':
    _main()
