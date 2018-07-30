from scipy import optimize
import numpy
from collections import OrderedDict
import json

required_materials = {
    'water': 0,
    'food': 300,
    'wood': 300,
    'stone': 300,
    'iron': 300
}

have = {
    'water': 440,
    'food': 769,
    'wood': 28, 
    'stone': 110,
    'iron': 409
}

short = {
    'water': 1100,
    'food': 2800,
    'wood': 300,
    'stone': 2800,
    'iron': 1700
}

required_materials = {}
for mat, num in short.items():
    required_materials[mat] = max(num - have[mat], 0)

with open('2018 Summer Part 1/currency_drops_parsed.json') as f:
    data = json.decoder.JSONDecoder().decode(f.read())

def drops(location, water=0, food=0, wood=0, stone=0, iron=0):
    location_drops = data[location + ' storm']
    drops = {}
    mapping = {
        'water': water,
        'food': food,
        'wood': wood,
        'stone': stone,
        'iron': iron
    }
    for mat, bonus in mapping.items():
        if mat in location_drops:
            drops[mat] = location_drops[mat][bonus]
        elif bonus != 0:
            print('='*10)
            print('Servant/CE warning: You have a', mat, 'bonus but', location, 'does not drop', mat+'!')
            print('='*10)
    return drops

summertime_mistresses = s = 4
wood_ces = w = 1

materials_per_run = OrderedDict((
    # assuming +6 bonus on each single material, and +2 of each for mountains.
    ('beach', drops('beach', water=6+s, food=0+s)),
    ('forest', drops('forest', food=6+s, water=0+s)), # Primeval Forest
    ('jungle', drops('jungle', wood=6+w, food=0+s)), # Jungle
    ('field', drops('field', stone=6, food=0+s)), # Grassfields
    ('cave', drops('cavern', iron=6, water=0+s)),
    ('mountains', drops('mountains', wood=2+w, stone=2, iron=2)),
))

def ap_required(params, log=False):
    ratios = {}
    for i, loc in enumerate(materials_per_run):
        ratios[loc] = params[i]
    materials_per_iteration = {}
    for loc, drops in materials_per_run.items():
        for mat, mat_drops in drops.items():
            if mat not in materials_per_iteration:
                materials_per_iteration[mat] = 0
            materials_per_iteration[mat] += ratios[loc] * mat_drops

    required_iterations = 0
    limiting = None
    for mat, drops_per_iter in materials_per_iteration.items():
        multiplier = required_materials[mat] / drops_per_iter
        if multiplier > required_iterations:
            required_iterations = multiplier
            limiting = mat
    if log:
        print(materials_per_run)
        print('=== Results ===')
        # print('final materials')
        # for mat, drops in materials_per_iteration.items():
        #     print(' ', mat, drops*required_iterations)
        print('Required Runs:')
        for loc, r in ratios.items():
            print(('  '+loc.title()).ljust(12), '{:>8.2f}'.format(r*required_iterations))
    return required_iterations*40*sum(params)

def _main():
    n = len(materials_per_run)
    bounds = optimize.Bounds([0]*n, [numpy.inf]*n, True)
    result = optimize.minimize(ap_required, [10]*n, method='SLSQP', bounds=bounds)
    #print(result)
    print('Required AP:  '+ '{:7.2f}'.format(ap_required(result.x, True)))

if __name__ == '__main__':
    _main()
    