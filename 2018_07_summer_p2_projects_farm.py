from fgo_tools import *
from fgo_tools import _json
from fgo_tools_experimental import SummerProjectsOptimiser2

import sys
import os
import json
import math
from collections import OrderedDict, defaultdict

def _main(n=100):
    os.chdir(os.path.dirname(__file__) + '/2018_07_summer')
    
    with open('part_2_drops.json', encoding='utf-8') as f:
        raw_data = json.decoder.JSONDecoder().decode(f.read())
    data = DropsData(raw_data)

    with open('optimised_part_2_projects.json', encoding='utf-8') as f:
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

    all_farming_nodes = [farming_nodes_1, farming_nodes_2]

    SELECTED_INDEX = 0

    these_nodes = all_farming_nodes[SELECTED_INDEX]
    required = Items(project_data[SELECTED_INDEX]['required_materials'])
    
    event_opt = EventOptimiser()

    parties = {}
    for loc in these_nodes:
        parties[loc] = data.best_party(loc, available)

    if SELECTED_INDEX == 1:
        parties['contaminated explosion'] = PartySetup(servants=Items(silver=2, gold=2, blue=2))
    for loc, party_setup in parties.items():
        for type_ in party_setup:
            parties[loc][type_] = \
                [x.friendly_name(True) for x in parties[loc][type_]]

    AP = 30 if SELECTED_INDEX == 0 else 40

    event_opt.set_current(Items(
        blue=45,
        gold=0,
        silver=45,
        cement=44,
        oil=120
    ))
    event_opt.set_target(required + Items(
        blue=0,
        gold=0,
        silver=0,
        cement=0,
        oil=0
    ))
    event_opt.set_farming_nodes(these_nodes)

    runs = event_opt.optimise_runs()
    result_text = _json({
        'party_setups': parties,
        'current': event_opt._current,
        'total_required': event_opt._target,
        'remaining': event_opt._remaining,
        'projects': project_data[SELECTED_INDEX]['projects'],
        'runs': runs,
        'ap': AP*sum(runs.values()),
    })
    print(_json({
        'projects': project_data[SELECTED_INDEX]['projects'],
        'runs': runs,
        'STAGE': SELECTED_INDEX,
        'ap': AP*sum(runs.values()),
        'total_runs': sum(runs.values())
    }))
    
    with open('optimised_part_2_projects_farm.json', 'w') as f:
        f.write((result_text))
    


if __name__ == '__main__':
    if len(sys.argv) > 1:
        print('Executing', sys.argv[1], 'iterations.')
        _main(int(sys.argv[1]))
    else:
        _main()