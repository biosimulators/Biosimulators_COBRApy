""" Data model for mapping KiSAO terms for algorithms and their parameters
to COBRApy methods and their arguments

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-31
:Copyright: 2020, BioSimulators Team
:License: MIT
"""

from biosimulators_utils.data_model import ValueType
import cobra.flux_analysis
import collections
import enum

__all__ = ['Solver', 'KISAO_ALGORITHMS_PARAMETERS_MAP']


class Solver(str, enum.Enum):
    """ Solver """
    cplex = 'cplex'
    glpk = 'glpk'
    gurobi = 'gurobi'


KISAO_ALGORITHMS_PARAMETERS_MAP = collections.OrderedDict([
    ('KISAO_0000437', {
        'kisao_id': 'KISAO_0000437',
        'name': 'flux-balance analysis (FBA)',
        'method': lambda model, **args: model.optimize(**args),
        'parameters': {
            'KISAO_0000553':  {
                'name': 'solver',
                'description': 'Convex optimization solver to use (e.g., CPLEX, GLPK).',
                'model_arg': 'solver',  # "CPLEX", "GLPK", "Gurobi"
                'type': ValueType.string,
                'enum': Solver,
            }
        },
        'check_status': True,
        'variables': [
            {
                'description': 'objective value',
                'target_type': 'objective',
                'target': r'^/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective(\[.*?\])?(/@value)?$',
                'get_target_results_paths': lambda model, active_obj_fbc_id, objective_sbml_fbc_ids:
                    (
                        [
                            (None, objective_sbml_fbc_id, None,
                                'objective_value' if objective_sbml_fbc_id == active_obj_fbc_id else None, None)
                            for objective_sbml_fbc_id in objective_sbml_fbc_ids
                        ] +
                        [
                            (None, objective_sbml_fbc_id, 'value',
                                'objective_value' if objective_sbml_fbc_id == active_obj_fbc_id else None, None)
                            for objective_sbml_fbc_id in objective_sbml_fbc_ids
                        ]
                    ),
            },
            {
                'description': 'reaction flux',
                'target_type': 'reaction',
                'target': r'^/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction(\[.*?\])?(/@flux)?$',
                'get_target_results_paths': lambda model, active_obj_fbc_id, objective_sbml_fbc_ids:
                    [
                        ('R_' + reaction.id, None, None, 'fluxes', (reaction.id,))
                        for reaction in model.reactions
                    ] +
                    [
                        ('R_' + reaction.id, None, 'flux', 'fluxes', (reaction.id,))
                        for reaction in model.reactions
                    ] +
                    [
                        (reaction.id, None, None, 'fluxes', (reaction.id,))
                        for reaction in model.reactions
                    ] +
                    [
                        (reaction.id, None, 'flux', 'fluxes', (reaction.id,))
                        for reaction in model.reactions
                    ],
            },
            {
                'description': 'reaction reduced cost',
                'target_type': 'reaction',
                'target': r'^/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction(\[.*?\])?/@reducedCost$',
                'get_target_results_paths': lambda model, active_obj_fbc_id, objective_sbml_fbc_ids:
                    [
                        ('R_' + reaction.id, None, 'reducedCost', 'reduced_costs', (reaction.id,))
                        for reaction in model.reactions
                    ] +
                    [
                        (reaction.id, None, 'reducedCost', 'reduced_costs', (reaction.id,))
                        for reaction in model.reactions
                    ],
            },
            {
                'description': 'species shadow price',
                'target_type': 'species',
                'target': r'^/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species(\[.*?\])?(/@shadowPrice)?$',
                'get_target_results_paths': lambda model, active_obj_fbc_id, objective_sbml_fbc_ids:
                    [
                        ('M_' + metabolite.id, None, None, 'shadow_prices', (metabolite.id,))
                        for metabolite in model.metabolites
                    ] +
                    [
                        ('M_' + metabolite.id, None, 'shadowPrice', 'shadow_prices', (metabolite.id,))
                        for metabolite in model.metabolites
                    ] +
                    [
                        (metabolite.id, None, None, 'shadow_prices', (metabolite.id,))
                        for metabolite in model.metabolites
                    ] +
                    [
                        (metabolite.id, None, 'shadowPrice', 'shadow_prices', (metabolite.id,))
                        for metabolite in model.metabolites
                    ],
            },
        ]
    }),
    ('KISAO_0000528', {
        'kisao_id': 'KISAO_0000528',
        'name': 'parsimonious flux-balance analysis (pFBA)',
        'method': cobra.flux_analysis.pfba,
        'parameters': {
            'KISAO_0000531': {
                'name': 'fraction of optimum',
                'description': 'Lower bound on the objective value relative to the optimal FBA solution.',
                'alg_arg': 'fraction_of_optimum',
                'type': ValueType.float,
            },
            'KISAO_0000553': {
                'name': 'solver',
                'description': 'Convex optimization solver to use (e.g., CPLEX, GLPK).',
                'model_arg': 'solver',
                'type': ValueType.string,
                'enum': Solver,
            },
        },
        'check_status': True,
        'variables': [
            {
                'description': 'objective value',
                'target_type': 'objective',
                'target': r'^/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective(\[.*?\])?(/@value)?$',
                'get_target_results_paths': lambda model, active_obj_fbc_id, objective_sbml_fbc_ids:
                    (
                        [
                            (None, objective_sbml_fbc_id, None,
                                'objective_value' if objective_sbml_fbc_id == active_obj_fbc_id else None, None)
                            for objective_sbml_fbc_id in objective_sbml_fbc_ids
                        ] +
                        [
                            (None, objective_sbml_fbc_id, 'value',
                                'objective_value' if objective_sbml_fbc_id == active_obj_fbc_id else None, None)
                            for objective_sbml_fbc_id in objective_sbml_fbc_ids
                        ]
                    ),
            },
            {
                'description': 'reaction flux',
                'target_type': 'reaction',
                'target': r'^/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction(\[.*?\])?(/@flux)?$',
                'get_target_results_paths': lambda model, active_obj_fbc_id, objective_sbml_fbc_ids:
                    [
                        ('R_' + reaction.id, None, None, 'fluxes', (reaction.id,))
                        for reaction in model.reactions
                    ] +
                    [
                        ('R_' + reaction.id, None, 'flux', 'fluxes', (reaction.id,))
                        for reaction in model.reactions
                    ] +
                    [
                        (reaction.id, None, None, 'fluxes', (reaction.id,))
                        for reaction in model.reactions
                    ] +
                    [
                        (reaction.id, None, 'flux', 'fluxes', (reaction.id,))
                        for reaction in model.reactions
                    ],
            },
            {
                'description': 'reaction reduced cost',
                'target_type': 'reaction',
                'target': r'^/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction(\[.*?\])?/@reducedCost$',
                'get_target_results_paths': lambda model, active_obj_fbc_id, objective_sbml_fbc_ids:
                    [
                        ('R_' + reaction.id, None, 'reducedCost', 'reduced_costs', (reaction.id,))
                        for reaction in model.reactions
                    ] +
                    [
                        (reaction.id, None, 'reducedCost', 'reduced_costs', (reaction.id,))
                        for reaction in model.reactions
                    ],
            },
            {
                'description': 'species shadow price',
                'target_type': 'species',
                'target': r'^/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species(\[.*?\])?(/@shadowPrice)?$',
                'get_target_results_paths': lambda model, active_obj_fbc_id, objective_sbml_fbc_ids:
                    [
                        ('M_' + metabolite.id, None, None, 'shadow_prices', (metabolite.id,))
                        for metabolite in model.metabolites
                    ] +
                    [
                        ('M_' + metabolite.id, None, 'shadowPrice', 'shadow_prices', (metabolite.id,))
                        for metabolite in model.metabolites
                    ] +
                    [
                        (metabolite.id, None, None, 'shadow_prices', (metabolite.id,))
                        for metabolite in model.metabolites
                    ] +
                    [
                        (metabolite.id, None, 'shadowPrice', 'shadow_prices', (metabolite.id,))
                        for metabolite in model.metabolites
                    ],
            },
        ]
    }),
    ('KISAO_0000527', {
        'kisao_id': 'KISAO_0000527',
        'name': 'geometric flux-balance analysis (gFBA)',
        'method': cobra.flux_analysis.geometric_fba,
        'parameters': {
            'KISAO_0000209': {
                'name': 'epsilon',
                'description': 'Convergence tolerance.',
                'alg_arg': 'epsilon',
                'type': ValueType.float,
            },
            'KISAO_0000486': {
                'name': 'max tries',
                'description': 'Maximum number of iterations.',
                'alg_arg': 'max_tries',
                'type': ValueType.integer,
            },
            'KISAO_0000529': {
                'name': 'processes',
                'description': 'Number of parallel processes to execute.',
                'alg_arg': 'processes',
                'type': ValueType.integer,
            },
            'KISAO_0000553': {
                'name': 'solver',
                'description': 'Convex optimization solver to use (e.g., CPLEX, GLPK).',
                'model_arg': 'solver',
                'type': ValueType.string,
                'enum': Solver,
            },
        },
        'check_status': True,
        'variables': [
            {
                'description': 'objective value',
                'target_type': 'objective',
                'target': r'^/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective(\[.*?\])?(/@value)?$',
                'get_target_results_paths': lambda model, active_obj_fbc_id, objective_sbml_fbc_ids:
                    (
                        [
                            (None, objective_sbml_fbc_id, None,
                                'objective_value' if objective_sbml_fbc_id == active_obj_fbc_id else None, None)
                            for objective_sbml_fbc_id in objective_sbml_fbc_ids
                        ] +
                        [
                            (None, objective_sbml_fbc_id, 'value',
                                'objective_value' if objective_sbml_fbc_id == active_obj_fbc_id else None, None)
                            for objective_sbml_fbc_id in objective_sbml_fbc_ids
                        ]
                    ),
            },
            {
                'description': 'reaction flux',
                'target_type': 'reaction',
                'target': r'^/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction(\[.*?\])?(/@flux)?$',
                'get_target_results_paths': lambda model, active_obj_fbc_id, objective_sbml_fbc_ids:
                    [
                        ('R_' + reaction.id, None, None, 'fluxes', (reaction.id,))
                        for reaction in model.reactions
                    ] +
                    [
                        ('R_' + reaction.id, None, 'flux', 'fluxes', (reaction.id,))
                        for reaction in model.reactions
                    ] +
                    [
                        (reaction.id, None, None, 'fluxes', (reaction.id,))
                        for reaction in model.reactions
                    ] +
                    [
                        (reaction.id, None, 'flux', 'fluxes', (reaction.id,))
                        for reaction in model.reactions
                    ],
            },
            {
                'description': 'reaction reduced cost',
                'target_type': 'reaction',
                'target': r'^/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction(\[.*?\])?/@reducedCost$',
                'get_target_results_paths': lambda model, active_obj_fbc_id, objective_sbml_fbc_ids:
                    [
                        ('R_' + reaction.id, None, 'reducedCost', 'reduced_costs', (reaction.id,))
                        for reaction in model.reactions
                    ] +
                    [
                        (reaction.id, None, 'reducedCost', 'reduced_costs', (reaction.id,))
                        for reaction in model.reactions
                    ],
            },
            {
                'description': 'species shadow price',
                'target_type': 'species',
                'target': r'^/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species(\[.*?\])?(/@shadowPrice)?$',
                'get_target_results_paths': lambda model, active_obj_fbc_id, objective_sbml_fbc_ids:
                    [
                        ('M_' + metabolite.id, None, None, 'shadow_prices', (metabolite.id,))
                        for metabolite in model.metabolites
                    ] +
                    [
                        ('M_' + metabolite.id, None, 'shadowPrice', 'shadow_prices', (metabolite.id,))
                        for metabolite in model.metabolites
                    ] +
                    [
                        (metabolite.id, None, None, 'shadow_prices', (metabolite.id,))
                        for metabolite in model.metabolites
                    ] +
                    [
                        (metabolite.id, None, 'shadowPrice', 'shadow_prices', (metabolite.id,))
                        for metabolite in model.metabolites
                    ],
            },
        ]
    }),
    ('KISAO_0000526', {
        'kisao_id': 'KISAO_0000526',
        'name': 'flux variability analysis (FVA)',
        'method': cobra.flux_analysis.flux_variability_analysis,
        'parameters': {
            'KISAO_0000532': {
                'name': 'loopless',
                'description': 'Whether to return only loopless solutions.',
                'alg_arg': 'loopless',
                'type': ValueType.boolean,
            },
            'KISAO_0000531': {
                'name': 'fraction of optimum',
                'description': 'Lower bound on the objective value relative to the optimal FBA solution.',
                'alg_arg': 'fraction_of_optimum',
                'type': ValueType.float,
            },
            'KISAO_0000533': {
                'name': 'pFBA factor',
                'description': 'Upper bound on the total sum of absolute fluxes relative to the smallest feasible sum of absolute fluxes.',
                'alg_arg': 'pfba_factor',
                'type': ValueType.float,
            },
            'KISAO_0000529': {
                'name': 'processes',
                'description': 'Number of parallel processes to execute.',
                'alg_arg': 'processes',
                'type': ValueType.integer,
            },
            'KISAO_0000553': {
                'name': 'solver',
                'description': 'Convex optimization solver to use (e.g., CPLEX, GLPK).',
                'model_arg': 'solver',
                'type': ValueType.string,
                'enum': Solver,
            },
        },
        'check_status': False,
        'variables': [
            {
                'description': 'reaction flux',
                'target_type': 'reaction',
                'target': r'^/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction(\[.*?\])?/@minFlux?$',
                'get_target_results_paths': lambda model, active_obj_fbc_id, objective_sbml_fbc_ids:
                [
                    ('R_' + reaction.id, None, 'minFlux', 'loc', (reaction.id, 'minimum'))
                    for reaction in model.reactions
                ] +
                [
                    (reaction.id, None, 'minFlux', 'loc', (reaction.id, 'minimum'))
                    for reaction in model.reactions
                ],
            },
            {
                'description': 'reaction flux',
                'target_type': 'reaction',
                'target': r'^/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction(\[.*?\])?/@maxFlux?$',
                'get_target_results_paths': lambda model, active_obj_fbc_id, objective_sbml_fbc_ids:
                [
                    ('R_' + reaction.id, None, 'maxFlux', 'loc', (reaction.id, 'maximum'))
                    for reaction in model.reactions
                ] +
                [
                    (reaction.id, None, 'maxFlux', 'loc', (reaction.id, 'minimum'))
                    for reaction in model.reactions
                ],
            },
        ],
    }),
])
