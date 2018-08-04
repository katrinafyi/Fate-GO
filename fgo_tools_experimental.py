from fgo_tools import *

import platypus

from collections import defaultdict, OrderedDict

class SummerProjectsOptimiser2:
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
            self._current_chunk = chunk
            self._chunk_projects = [proj for group in chunk for proj in group]
            result.append(self._optimise_one_chunk(
                chunk,
                self._all_farming_nodes[i]
            ))
        return result if self._chunked else result[0]

    def _constrain_projects(self, input_vars):
        output = []
        start = 0
        for group in self._current_chunk:
            end = start + len(group)
            output.append(sum(input_vars[start:end]))
            start = end
        return output

    def _problem_function(self, input_vars):
        constraints = self._constrain_projects(input_vars)
        if any(x != 1 for x in constraints):
            return (0, constraints)
        
        required = Items()
        for i, p in enumerate(input_vars):
            if p:
                required += Items(self._chunk_projects[i]['cost'])
        self._event_opt.set_target(required)

        return (sum(self._event_opt.optimise_runs().values()), 
            constraints)

    def _calculate_required(self, variables):
        required = Items()
        for i, x in enumerate(variables):
            if x[0]:
                required += self._chunk_projects[i]['cost']
        return required

    def _optimise_one_chunk(self, chunk, nodes):
        event_opt = self._event_opt
        event_opt.set_farming_nodes(nodes)

        n_variables = sum(len(x) for x in chunk)
        n_constraints = len(chunk)

        problem = platypus.Problem(n_variables, 1, n_constraints)
        problem.types[:] = platypus.Integer(0, 1)
        problem.constraints[:] = '==1'
        problem.function = self._problem_function
        problem.directions[:] = platypus.Problem.MINIMIZE

        algorithm = platypus.NSGAII(problem)
        algorithm.run(20000)

        possible_results = [s for s in algorithm.result if s.feasible]
        possible_results.sort(key=lambda x: self._calculate_required(x.variables).magnitude(), reverse=True)
        possible_results.sort(key=lambda x: x.objectives[0])
        possible_results.sort(key=lambda x: x.constraint_violation)

        if not possible_results:
            print('No feasible solutions.')
            return

        required = self._calculate_required(possible_results[0].variables)
        event_opt.set_target(required)
        runs = event_opt.optimise_runs()

        current_items = event_opt.total_items(runs) + event_opt._current
        event_opt.set_current(current_items-required)

        return {
            'projects': [self._chunk_projects[i]['name'] for i, s in enumerate(possible_results[0].variables) if s[0]],
            'required_materials': required,
            'runs': runs,
            'total_runs': sum(runs.values()),
            'ap': 40*sum(runs.values()),
        }
