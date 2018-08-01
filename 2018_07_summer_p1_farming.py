from collections import OrderedDict
import json
import os

from fgo_tools import *
from fgo_tools import _json

def _main():
    os.chdir(os.path.dirname(__file__) + '/2018_07_summer')
    with open('part_1_drops.json') as f:
        raw_data = json.decoder.JSONDecoder().decode(f.read())
    data = DropsData(raw_data)

    my_servants = [
        Items(food=1), 
        Items(water=1),
        Items(wood=1),
        Items(stone=1),
        Items(iron=1)
    ]*6

    summertime_mistresses = s = 5
    wood_ces = w = 1

    my_ces = [Items(food=1, water=1)] * s + [Items(wood=1)] * w

    available_supports = [
        Items(food=2, water=1), 
        Items(food=1, water=2),
        Items(wood=2),
        Items(stone=2),
        Items(iron=2)
    ]

    

    locations = ['beach storm', 'forest storm', 
        'jungle storm', 'field storm', 'cavern storm']

    parties = OrderedDict()

    drops_per_run = OrderedDict()
    for loc in locations:
        p = data.best_party(loc, my_servants, my_ces, 
            available_supports)
        drops_per_run[loc] = data.drops_with_party(loc, p)
        parties[loc] = p
    parties['mountains storm'] = PartySetup(
        servants=[Items(wood=1), Items(stone=1), Items(iron=1)]*2,
        craft_essences=[Items(wood=1)],
    )
    drops_per_run['mountains storm'] = data.drops_with_bonus(
        'mountains storm', Items(wood=3, stone=2, iron=2))

    event_opt = EventOptimiser()
    event_opt.set_current(Items(
        water=530,
        food=1084,
        wood=40,
        stone=938,
        iron=512
    ))
    event_opt.set_target(Items(
        water=1100,
        food=2800,
        wood=300,
        stone=2800,
        iron=1600-80
    ))
    event_opt.set_farming_nodes(drops_per_run)

    for loc, party_setup in parties.items():
        for type_ in party_setup:
            parties[loc][type_] = \
                [x.friendly_name() for x in parties[loc][type_]]


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

    with open('part_1_optimised.json', 'w') as f:
        f.write(result_text)



if __name__ == '__main__':
    _main()
    