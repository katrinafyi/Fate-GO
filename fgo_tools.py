from collections import OrderedDict, defaultdict
from typing import Union
import json
import math

from ortools.linear_solver import pywraplp

__all__ = ['Items', 'PartySetup', 'DropsData', 'EventOptimiser',
    'SummerProjectsOptimiser']

_json_encoder = None

def _json(obj):
    global _json_encoder
    if _json_encoder is None:
        _json_encoder = json.encoder.JSONEncoder(indent=2)
    return _json_encoder.encode(obj)

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

    def friendly_name(self, is_bonus=False):
        plus = '+' if is_bonus else ''
        bonus_strings = [plus+str(n)+' '+x for x, n in self.items() if n != 0]
        if not bonus_strings:
            return plus+'0'
        return ', '.join(bonus_strings)

class PartySetup(dict):
    def __init__(self, servants=None, craft_essences=None, support=None):
        if servants is None:
            servants = []
        if craft_essences is None:
            craft_essences = []
        if support is None:
            support = []
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

    def best_party(self, location, available: PartySetup=None, priorities=None):
        supports = available['support']
        servants = available['servants']
        craft_essences = available['craft_essences']
        if priorities is None:
            stacks = self.stacks(location)
            priorities = list(sorted(self.drops_with_bonus(location),
                key=lambda x: stacks[x], reverse=True))
        
        for p in reversed(priorities):
            servants = sorted(servants, key=lambda x: x[p], reverse=True)
            supports = sorted(supports, key=lambda x: x[p], reverse=True)
            craft_essences = sorted(craft_essences, key=lambda x: x[p], reverse=True)

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

    def best_drops(self, location, available_parties):
        return self.drops_with_party(location, self.best_party(
            location, available_parties
        ))

    def optimise_drops(self, location_list, available_parties):
        drops_per_run = OrderedDict()
        for loc in location_list:
            drops_per_run[loc] = self.best_drops(loc, available_parties)
        return drops_per_run


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

    def _do_optimise(self, use_int=True):
        if use_int:
            solver = pywraplp.Solver('IntegerSolver', 
                pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING) 
        else:
            solver = pywraplp.Solver('LinearSolver',
                pywraplp.Solver.GLOP_LINEAR_PROGRAMMING)

        make_var = solver.IntVar if use_int else solver.NumVar

        node_vars = []
        for loc in self._farming_nodes:
            node_vars.append(make_var(0, solver.infinity(), loc))

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


class SummerProjectsOptimiser:
    def __init__(self, chunked=False):
        self._chunked = chunked
        self._available = PartySetup()
        self._all_projects = []
        self._all_farming_nodes = []

    def set_projects(self, projects: OrderedDict):
        if self._chunked:
            self._all_projects = projects
        else:
            self._all_projects = [projects]

    def set_farming_nodes(self, nodes):
        if self._chunked:
            self._all_farming_nodes = nodes
        else:
            self._all_farming_nodes = [nodes]

    def optimise_projects(self):
        self._event_opt = EventOptimiser()
        result = []
        for i, chunk in enumerate(self._all_projects):
            result.append(self._optimise_one_chunk(
                chunk,
                self._all_farming_nodes[i]
            ))
        return result if self._chunked else result[0]

    @staticmethod
    def calculate_item_weights(nodes):
        weights = defaultdict(lambda: 0)
        for loc, drops in nodes.items():
            for drop, num in drops.items():
                import math
                weights[drop] += num
        return weights

    def _optimise_one_chunk(self, chunk, nodes):
        event_opt = self._event_opt
        event_opt.set_farming_nodes(nodes)

        temp_current = event_opt._current
        event_opt.set_current(Items())
        
        # total items from running each node once.
        mats_per_iteration = self.calculate_item_weights(nodes)

        solver = pywraplp.Solver('SolveIntegerProblem', 
            pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
        objective = solver.Objective()

        project_list = []
        for i, project_group in enumerate(chunk):
            constraint = solver.Constraint(1, 1)
            for j, project in enumerate(project_group):
                var = solver.IntVar(0, 1, project['name'])
                constraint.SetCoefficient(var, 1)

                event_opt.set_target(project['cost'])
                runs_required = event_opt._do_optimise(use_int=False)

                coeff = sum(runs_required)
                objective.SetCoefficient(var, coeff)

                project_list.append([project, var])

        objective.SetMinimization()
        assert solver.Solve() == solver.OPTIMAL

        projects_to_do = [proj for proj, var in project_list if var.solution_value()]

        required = Items()
        for proj in projects_to_do:
            for mat, num in proj['cost'].items():
                required[mat] += num

        event_opt.set_current(temp_current)
        event_opt.set_target(required)
        runs = event_opt.optimise_runs()

        current_items = event_opt.total_items(runs) + event_opt._current
        event_opt.set_current(current_items-required)

        return {
            'projects': [p['name'] for p in projects_to_do],
            'required_materials': required,
            'runs': runs,
            'total_runs': sum(runs.values()),
            'ap': 40*sum(runs.values()),
        }
