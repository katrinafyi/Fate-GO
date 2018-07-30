from scipy import optimize
import numpy
from collections import OrderedDict
import json
import typing
import types

class Items(dict):
    def __init__(self, water=0, food=0, wood=0, stone=0, iron=0):
        mapping = {
            'water': water,
            'food': food,
            'wood': wood,
            'stone': stone,
            'iron': iron
        }
        for k, v in mapping.items():
            setattr(self, k, v)
        super().__init__(mapping)

class EventOptimiser:

    def __init__(self):
        self._required = Items()
        self._target = Items()
        self._current = Items()
        self._farming_nodes = OrderedDict()

    def _update_required(self):
        self._required.clear()
        for mat, num in self._target.items():
            self._required[mat] = max(num - self._current[mat], 0)

    def set_target(self, items: Items):
        self._target = items
        self._update_required()

    def set_current(self, items: Items):
        self._current = items
        self._update_required()

    def set_farming_nodes(self, nodes):
        self._farming_nodes = nodes

    def _runs_required(self, node_ratios):
        ratios = self._to_dict(node_ratios)
        drops_per_iteration = self.total_items(ratios)

        required_iterations = 0
        for mat, drops_per_iter in drops_per_iteration.items():
            multiplier = self._required[mat] / drops_per_iter
            if multiplier > required_iterations:
                required_iterations = multiplier

        return [required_iterations*x for x in node_ratios]

    def _ap_required(self, node_ratios):
        runs = self._runs_required(node_ratios)
        return 40*sum(runs)

    def _to_dict(self, array):
        d = {}
        for i, key in enumerate(self._farming_nodes):
            d[key] = array[i]
        return d

    def _do_optimise(self):
        n = len(self._farming_nodes)
        bounds = optimize.Bounds([0]*n, [numpy.inf]*n, True)
        return optimize.minimize(self._ap_required, [10]*n, 
            method='SLSQP', bounds=bounds)

    def optimise_runs(self):
        result = self._do_optimise()
        return self._to_dict(self._runs_required(result.x))

    def total_items(self, nodes_farmed):
        total = {}
        for loc, times in nodes_farmed.items():
            for mat, mat_drops in self._farming_nodes[loc].items():
                if mat not in total:
                    total[mat] = 0
                total[mat] += times * mat_drops
        return total

class DropsData: 
    def __init__(self, data):
        self._data = data

    def drops(self, location, bonuses: Items=None, **kwargs):
        location_drops = self._data[location]
        drops = {}
        if bonuses is None:
            bonuses = Items(**kwargs)

        for item, bonus in bonuses.items():
            if item in location_drops:
                drops[item] = location_drops[item][bonus]
            elif bonus != 0:
                raise Warning(
                    'Servant/CE warning: You have a '+item+' bonus but '+location+' does not drop '+item+'!')
        return drops

def _main():
    with open('2018 Summer Part 1/currency_drops_parsed.json') as f:
        raw_data = json.decoder.JSONDecoder().decode(f.read())
    data = DropsData(raw_data)

    summertime_mistresses = s = 4
    wood_ces = w = 1

    nodes = OrderedDict((
        # assuming +6 bonus on each single material, and +2 of each for mountains.
        ('beach', data.drops('beach storm', water=6+s, food=0+s)),
        ('forest', data.drops('forest storm', food=6+s, water=0+s)), # Primeval Forest
        ('jungle', data.drops('jungle storm', wood=6+w, food=0+s)), # Jungle
        ('field', data.drops('field storm', stone=6, food=0+s)), # Grassfields
        ('cave', data.drops('cavern storm', iron=6, water=0+s)),
        ('mountains', data.drops('mountains storm', wood=2+w, stone=2, iron=2)),
    ))

    event_opt = EventOptimiser()
    event_opt.set_current(Items(
        water=440,
        food=769,
        wood=28,
        stone=110,
        iron=409
    ))
    event_opt.set_target(Items(
        water=1100,
        food=2800,
        wood=300,
        stone=2800,
        iron=1700
    ))
    event_opt.set_farming_nodes(nodes)

    runs = event_opt.optimise_runs()
    print(runs)
    print('Required AP:', 40*sum(runs.values()))
    print()
    print('Materials')
    print(event_opt._required)
    print(event_opt.total_items(runs))

if __name__ == '__main__':
    _main()
    