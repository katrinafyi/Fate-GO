from fgo_tools import *
from fgo_tools import _json
from ortools.linear_solver import pywraplp

import os
import json
import math
from collections import OrderedDict, defaultdict

def _set_farming_nodes(optimiser):
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

    summertime_mistresses = s = 0
    wood_ces = w = 0

    my_ces = [Items(food=1, water=1)] * s + [Items(wood=1)] * w

    available_supports = [
        Items(food=2, water=1), 
        Items(food=1, water=2),
        Items(wood=2),
        Items(stone=2),
        Items(iron=2)
    ]

    locations = ['beach thunder', 'forest thunder', 
        'jungle thunder', 'field thunder', 'cavern thunder']

    parties = OrderedDict()

    drops_per_run = OrderedDict()
    for loc in locations:
        p = data.best_party(loc, PartySetup(my_servants, my_ces, 
            available_supports))
        drops_per_run[loc] = data.drops_with_party(loc, p)
        parties[loc] = p
    parties['mountains thunder'] = PartySetup(
        servants=[Items(wood=1), Items(stone=1), Items(iron=1)]*2,
    )
    drops_per_run['mountains thunder'] = data.drops_with_bonus(
        'mountains thunder', Items(wood=2, stone=2, iron=2))

    optimiser.set_farming_nodes(drops_per_run)
    return drops_per_run


def _main():
    os.chdir(os.path.dirname(__file__) + '/2018_07_summer')
    
    with open('part_1_projects.json') as f:
        project_data = json.decoder.JSONDecoder().decode(f.read())

    optimiser = EventOptimiser()

    solver = pywraplp.Solver('SolveIntegerProblem', 
        pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    nodes = _set_farming_nodes(optimiser)
    mats_per_iteration = optimiser.total_items({
        x: 1 for x in nodes
    })
    #print(_json(mats_per_iteration))
    #mats_per_iteration = defaultdict(lambda: 1)

    objective = solver.Objective()

    constraints = {}
    var_list = []
    for project_name, project_required in project_data.items():
        proj_num = project_name.split(' ')[1]
        if proj_num not in constraints:
            constraints[proj_num] = solver.Constraint(1, 1)

        var = solver.IntVar(0, 1, project_name)
        constraints[proj_num].SetCoefficient(var, 1)


        coeff = 0
        for mat, num in project_required.items():
            coeff += num #/ (mats_per_iteration[mat])
        objective.SetCoefficient(var, coeff)

        var_list.append(var)

    objective.SetMinimization()
    assert solver.Solve() == solver.OPTIMAL

    projects_to_do = [var.name() for var in var_list if var.solution_value()]
    print((projects_to_do))
    print(_json(mats_per_iteration))

    required = defaultdict(lambda: 0)

    for proj in projects_to_do:
        for mat, num in project_data[proj].items():
            required[mat] += num

    #print(_json(required))

    optimiser.set_target(required)

    runs = optimiser.optimise_runs()
    print(_json({
        'runs': runs,
        'ap': 40*sum(runs.values())
    }))


if __name__ == '__main__':
    _main()
