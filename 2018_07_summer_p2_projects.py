from fgo_tools import *
from fgo_tools import _json
from ortools.linear_solver import pywraplp

import os
import json
import math
from collections import OrderedDict, defaultdict

def _get_farming_nodes(optimiser):
    with open('part_2_drops.json', encoding='utf-8') as f:
        raw_data = json.decoder.JSONDecoder().decode(f.read())
    data = DropsData(raw_data)

    my_servants = [
        Items(blue=1), 
        Items(gold=1),
        Items(silver=1),
        Items(oil=1),
        Items(cement=1)
    ]*6

    summertime_mistresses = s = 0
    wood_ces = w = 0

    my_ces = []

    available_supports = [
        Items(food=2), 
        Items(water=2),
        Items(wood=2),
        Items(stone=2),
        Items(iron=2)
    ]

    def optimise_drops(locations):
        drops_per_run = OrderedDict()
        for loc in locations:
            p = data.best_party(loc, my_servants, my_ces, 
                available_supports)
            drops_per_run[loc] = data.drops_with_party(loc, p)
        return drops_per_run

    
    last_drops = optimise_drops(['underworld explosion', 
        'fields explosion', 'coast explosion', 'cave explosion',
        'city explosion'])
    last_drops['contaminated explosion'] = data.drops_with_bonus(
        'contaminated explosion', Items(silver=2, gold=2, blue=2)
    )

    return [
        optimise_drops(['underworld advanced', 
            'fields advanced', 'coast advanced', 'cave advanced']),
        last_drops
    ]


def _main():
    os.chdir(os.path.dirname(__file__) + '/2018_07_summer')
    
    with open('part_2_projects.json', encoding='utf-8') as f:
        project_data = json.decoder.JSONDecoder().decode(f.read())

    optimiser = EventOptimiser()

    

    checkpoints = ['Project 5 C']
    respective_nodes = _get_farming_nodes(optimiser)

    mats_iteration_list = []
    for x in respective_nodes:
        optimiser.set_farming_nodes(x)
        mats_iteration_list.append(optimiser.total_items({
            y: 1 for y in x
        }))
    #print(_json(mats_per_iteration))
    #mats_per_iteration = defaultdict(lambda: 1)

    solver = pywraplp.Solver('SolveIntegerProblem', 
        pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    objective = solver.Objective()


    constraints = {}
    var_list = []
    current_checkpoint = 0
    checkpoints.append(list(project_data.keys())[-1])
    for i, (project_name, project_required) in enumerate(project_data.items()):
        proj_num = int(project_name.split(' ')[1])
        if proj_num not in constraints:
            constraints[proj_num] = solver.Constraint(1, 1)

        var = solver.IntVar(0, 1, project_name)
        constraints[proj_num].SetCoefficient(var, 1)

        mats_per_iteration = mats_iteration_list[current_checkpoint]

        coeff = 0
        for mat, num in project_required.items():
            coeff += num / (mats_per_iteration[mat])
        objective.SetCoefficient(var, coeff)

        var_list.append(var)

        if project_name in checkpoints:
            print(mats_per_iteration)
            # print('Stopping at', proj_num, project_name)
            # current_checkpoint += 1
            # continue
            objective.SetMinimization()
            assert solver.Solve() == solver.OPTIMAL

            projects_to_do = [var.name() for var in var_list if var.solution_value()]
            print((projects_to_do))
            print('per_iteration:', (mats_per_iteration))

            required = Items()

            for proj in projects_to_do:
                for mat, num in project_data[proj].items():
                    required[mat] += num

            optimiser.set_farming_nodes(respective_nodes[current_checkpoint])
            optimiser.set_target(required)
            runs = optimiser.optimise_runs()


            print('required:', (required))
            obtained = optimiser.total_items(runs) + optimiser._current
            print('obtained:', obtained)
            print('extra:', obtained-(required))

            

            print(_json({
                'runs': runs,
                'total_runs': sum(runs.values()),
                'ap': 40*sum(runs.values()),
                
            }))
            

            solver = pywraplp.Solver('SolveIntegerProblem', 
                pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
            objective = solver.Objective()
            var_list.clear()

            optimiser.set_current(obtained-required)
            current_checkpoint += 1


if __name__ == '__main__':
    _main()
