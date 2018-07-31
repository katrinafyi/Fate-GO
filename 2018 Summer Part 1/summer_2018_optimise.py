from collections import OrderedDict
import json
import os

from ortools.linear_solver import pywraplp


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

    def _runs_required(self, node_ratios):
        assert len(node_ratios) == len(self._farming_nodes)

        ratios = self._to_dict(node_ratios)
        drops_per_iteration = self.total_items(ratios)

        required_iterations = 0
        for mat, drops_per_iter in drops_per_iteration.items():
            multiplier = self._remaining[mat] / drops_per_iter
            if multiplier > required_iterations:
                required_iterations = multiplier

        return [required_iterations*x for x in node_ratios]

    def _ap_required(self, node_ratios):
        assert len(node_ratios) == len(self._farming_nodes)

        runs = self._runs_required(node_ratios)
        return 40*sum(runs)

    def _to_dict(self, array):
        assert len(array) == len(self._farming_nodes)
        d = {}
        for i, key in enumerate(self._farming_nodes):
            d[key] = array[i]
        return d

    def _do_optimise(self):
        solver = pywraplp.Solver('SolveIntegerProblem', 
            pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

        node_vars = []
        for loc in self._farming_nodes:
            node_vars.append(solver.IntVar(0, solver.infinity(), loc))

        n = len(self._farming_nodes)

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

    def best(location, supports=None, servants=None, craft_essences=None):
        if supports is None:
            supports = []
        if servants is None: 
            servants = []
        if craft_essences is None:
            craft_essences = []
        

def _main():
    os.chdir(os.path.dirname(__file__))
    with open('currency_drops_parsed.json') as f:
        raw_data = json.decoder.JSONDecoder().decode(f.read())
    data = DropsData(raw_data)

    summertime_mistresses = s = 5
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
        *(int(x) for x in ('482 874 40 377 482'.split(' ')))
    ))
    event_opt.set_target(Items(
        *(int(x) for x in ('1100 2800 300 2800 1600'.split(' ')))
    ))
    event_opt.set_farming_nodes(nodes)

    runs = event_opt.optimise_runs()
    result_text = json.encoder.JSONEncoder(indent=4).encode({
        'current': event_opt._current,
        'total_required': event_opt._target,
        'remaining': event_opt._remaining,
        'runs': runs,
        'ap': 40*sum(runs.values()),
    })
    print(result_text)

    with open('summer_2018_optimised.json', 'w') as f:
        f.write(result_text)



if __name__ == '__main__':
    _main()
    