from collections import OrderedDict
import json
import os

from fgo_tools import *
from fgo_tools import _json

def _main():
    os.chdir(os.path.dirname(__file__) + '/2018_07_summer')
    with open('part_2_drops.json') as f:
        raw_data = json.decoder.JSONDecoder().decode(f.read())
    data = DropsData(raw_data)

    my_servants = [
        Items(silver=1), 
        Items(gold=1),
        Items(blue=1),
        Items(cement=1),
        Items(oil=1)
    ]*4

    chaldea_lifesavers = c = 1
    wood_ces = w = 2

    my_ces = [Items(oil=1, cement=1)] * c + [Items(silver=1)] * w

    available_supports = [
        Items(oil=2, cement=1), 
        Items(oil=1, cement=2),
        Items(silver=2),
        Items(blue=2),
        Items(gold=2)
    ]

    locations = ['underworld destruction', 
        'fields destruction', 'coast destruction', 'cave destruction',
        'city destruction']

    avail = PartySetup(my_servants, my_ces, 
            available_supports)
    parties = {
        loc: data.best_party(loc, avail) for loc in locations
    }
    parties['contaminated destruction'] = PartySetup(
        servants=[Items(silver=1), Items(gold=1), Items(blue=1)]*2,
        craft_essences=[Items(silver=1)]*2,
    )

    drops_per_run = OrderedDict()
    for loc, p in parties.items():
        drops_per_run[loc] = data.drops_with_party(loc, p)

    event_opt = EventOptimiser()
    event_opt.set_current(Items(
        blue=587,
        gold=79,
        silver=740,
        cement=1554,
        oil=465+150
    ))
    end_target = Items(
        blue=1550+150,
        gold=0,
        silver=750+200+200,
        cement=2900+100+200,
        oil=1200+150+150,
    )
    event_opt.set_target(end_target)

        
    event_opt.set_farming_nodes(drops_per_run)

    for loc, party_setup in parties.items():
        for type_ in party_setup:
            parties[loc][type_] = \
                [x.friendly_name(True) for x in parties[loc][type_]]


    runs = event_opt.optimise_runs()
    result_text = _json({
        'party_setups': parties,
        'current': event_opt._current,
        'total_required': event_opt._target,
        'remaining': event_opt._remaining,
        'runs': runs,
        'ap': 40*sum(runs.values()),
    })
    print(_json({
        'runs': runs,
        'ap': 40*sum(runs.values()),
        'total_runs': sum(runs.values())
    }))

    with open('optimised_part_2_farming.json', 'w') as f:
        f.write(result_text)



if __name__ == '__main__':
    _main()
    