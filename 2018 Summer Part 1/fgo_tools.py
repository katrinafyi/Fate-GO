from collections import OrderedDict, defaultdict
import json
import os
from typing import Union

from ortools.linear_solver import pywraplp

class Items(defaultdict):
    def __init__(self, *args, **kwargs):
        super().__init__(lambda: 0, *args, **kwargs)

    def __add__(self, other):
        result = Items()
        for key in self:
            result[key] += self[key]
        for key in other:
            result[key] += other[key]
        return result

    def __neg__(self):
        result = Items()
        for key in self:
            result[key] = -self[key]
        return result

    def __sub__(self, other):
        return self + (-other)

    def __repr__(self):
        return self.__class__.__name__+'('+', '.join(
            x+'='+repr(y) for (x, y) in self.items() if y != 0) + ')'

    def non_zero(self):
        return any(x for x in self.values())

    def friendly_name(self):
        bonus_strings = ['+'+str(n)+' '+x for x, n in self.items() if n != 0]
        if not bonus_strings:
            return 'No event bonuses.'
        return ', '.join(bonus_strings)

class PartySetup(dict):
    def __init__(self, servants=None, craft_essences=None, support=None):
        if servants is None:
            servants = Items()
        if craft_essences is None:
            craft_essences = Items()
        if support is None:
            support = Items()
        self['servants'] = servants
        self['craft_essences'] = craft_essences
        self['support'] = support

    @property
    def servants(self):
        return self['servants']

    @property
    def craft_essences(self):
        return self['craft_essences']

    @property
    def support(self):
        return self['support']

    def total_bonus(self):
        return sum(self.servants + self.craft_essences + self.support, Items())


class EventOptimiser:
    def __init__(self):
        self._remaining = Items()
        self._target = Items()
        self._current = Items()
        self._farming_nodes = OrderedDict()

    def _update_remaining(self):
        self._remaining.clear()
        for mat, num in self._target.items():
            self._remaining[mat] = max(num - self._current[mat], 0)

    def set_target(self, items: Items):
        self._target = items
        self._update_remaining()

    def set_current(self, items: Items):
        self._current = items
        self._update_remaining()

    def set_farming_nodes(self, nodes):
        self._farming_nodes = nodes

    def _to_dict(self, array):
        assert len(array) == len(self._farming_nodes)
        d = OrderedDict()
        for i, key in enumerate(self._farming_nodes):
            d[key] = array[i]
        return d

    def _do_optimise(self):
        solver = pywraplp.Solver('SolveIntegerProblem', 
            pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

        node_vars = []
        for loc in self._farming_nodes:
            node_vars.append(solver.IntVar(0, solver.infinity(), loc))

        constraints = {}
        for i, drops in enumerate(self._farming_nodes.values()):
            for material, number in drops.items():
                if material not in constraints:
                    constraints[material] = solver.Constraint(
                        self._remaining[material], solver.infinity())
                    
                constraints[material].SetCoefficient(node_vars[i], number)

        objective = solver.Objective()
        for var in node_vars:
            objective.SetCoefficient(var, 1)
        objective.SetMinimization()

        status = solver.Solve()
        assert status == pywraplp.Solver.OPTIMAL
        assert solver.VerifySolution(1e-7, True)
        
        return [var.solution_value() for var in node_vars]

    def optimise_runs(self):
        result = self._do_optimise()
        return self._to_dict(result)

    def total_items(self, nodes_farmed):
        total = Items()
        for loc, times in nodes_farmed.items():
            for mat, mat_drops in self._farming_nodes[loc].items():
                total[mat] += times * mat_drops
        return total

class DropsData: 
    def __init__(self, data):
        self._data = data

    def drops_with_bonus(self, location, bonuses: Items=None):
        location_drops = self._data[location]
        if bonuses is None:
            bonuses = Items()

        drops = Items()
        for item, item_drops in location_drops.items():
            drops[item] = item_drops['initial'] + bonuses[item] * item_drops['stacks']
        return drops

    def drops_with_party(self, location, party: PartySetup):
        return self.drops_with_bonus(location, party.total_bonus())

    def stacks(self, location):
        ret = {}
        for item, item_data in self._data[location].items():
            ret[item] = item_data['stacks']
        return Items(ret)

    def best_party(self, location, servants=None, craft_essences=None, supports=None, priorities=None):
        if supports is None:
            supports = []
        if servants is None: 
            servants = []
        if craft_essences is None:
            craft_essences = []
        if priorities is None:
            stacks = self.stacks(location)
            priorities = list(sorted(self.drops_with_bonus(location),
                key=lambda x: stacks[x], reverse=True))
        
        for p in reversed(priorities):
            servants.sort(key=lambda x: x[p], reverse=True)
            supports.sort(key=lambda x: x[p], reverse=True)
            craft_essences.sort(key=lambda x: x[p], reverse=True)

        out = [[], [], []]

        for i, domain in enumerate((servants, craft_essences, supports)):
            for ent in domain:
                if any(ent[p] != 0 for p in priorities):
                    out[i].append(ent)

        return PartySetup(
            servants=out[0][:5],
            craft_essences=out[1][:5],
            support=out[2][:1]
        )

def _main():
    _json_encoder = json.encoder.JSONEncoder(indent=2)

    def _json(obj):
        return _json_encoder.encode(obj)

    os.chdir(os.path.dirname(__file__))
    with open('currency_drops_parsed_2.json') as f:
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
        water=482,
        food=979,
        wood=40,
        stone=641,
        iron=402
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

    with open('summer_2018_optimised.json', 'w') as f:
        f.write(result_text)



if __name__ == '__main__':
    _main()
    