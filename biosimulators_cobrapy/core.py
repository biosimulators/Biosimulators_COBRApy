""" Methods for executing SED tasks in COMBINE archives and saving their outputs

:Author: Author name <email@organization>
:Date: YYYY-MM-DD
:Copyright: YYYY, Owner
:License: <License, e.g., MIT>
"""

from Biosimulations_utils.simulation.data_model import SteadyStateSimulation, SimulationResultsFormat  # noqa: F401
from Biosimulations_utils.simulation.hdf5 import Hdf5SimulationResultsWriter
from Biosimulations_utils.simulator.utils import exec_simulations_in_archive
import cobra.flux_analysis
import cobra.io
import json
import numpy
import os
import pandas
import re

__all__ = ['exec_combine_archive', 'exec_simulation']


KISAO_ALGORITHMS_PARAMETERS_MAP = {
    'KISAO_0000437': {
        'method': lambda model, **args: model.optimize(**args),
        'default_args': {}
        'parameters': {
            'KISAO_0000553':  {
                'model_arg': 'solver',  # "CPLEX", "GLPK", "Gurobi"
                'parse_value': lambda solver: solver.lower(),
            }
        },
    },
    'KISAO_0000528': {
        'method': cobra.flux_analysis.pfba,
        'default_args': {},
        'parameters': {
            'KISAO_0000531': {
                'alg_arg': 'fraction_of_optimum',
            },
            'KISAO_0000553': {
                'model_arg': 'solver',
                'parse_value': lambda solver: solver.lower(),
            },
        },
    },
    'KISAO_0000527': {
        'method': cobra.flux_analysis.geometric_fba,
        'default_args': {},
        'parameters': {
            'KISAO_0000209': {
                'alg_arg': 'epsilon',
            },
            'KISAO_0000486': {
                'alg_arg': 'max_tries',
            },
            'KISAO_0000529': {
                'alg_arg': 'processes',
            }
            'KISAO_0000553': {
                'model_arg': 'solver',
                'parse_value': lambda solver: solver.lower(),
            },
        },
    },
    'KISAO_0000526': {
        'method': cobra.flux_analysis.flux_variability_analysis,
        'default_args': {},
        'parameters': {
            'KISAO_0000534': {
                'alg_arg': 'reaction_list',
                'parse_value': json.loads,
            },
            'KISAO_0000532': {
                'alg_arg': 'loopless',
            },
            'KISAO_0000531': {
                'alg_arg': 'fraction_of_optimum',
            },
            'KISAO_0000533': {
                'alg_arg': 'pfba_factor',
            },
            'KISAO_0000529': {
                'alg_arg': 'processes',
            }
            'KISAO_0000553': {
                'model_arg': 'solver',
                'parse_value': lambda solver: solver.lower(),
            },
        },
        'results_rows': ['lower', 'upper'],
    },
}


def exec_combine_archive(archive_file, out_dir):
    """ Execute the SED tasks defined in a COMBINE archive and save the outputs

    Args:
        archive_file (:obj:`str`): path to COMBINE archive
        out_dir (:obj:`str`): directory to store the outputs of the tasks
    """
    exec_simulations_in_archive(archive_file, exec_simulation, out_dir, apply_model_changes=True)


def exec_simulation(model_filename, model_sed_urn, simulation, working_dir, out_filename, out_format):
    ''' Execute a simulation and save its results

    Args:
       model_filename (:obj:`str`): path to the model
       model_sed_urn (:obj:`str`): SED URN for the format of the model (e.g., `urn:sedml:language:sbml`)
       simulation (:obj:`SteadyStateSimulation`): simulation
       working_dir (:obj:`str`): directory of the SED-ML file
       out_filename (:obj:`str`): path to save the results of the simulation
       out_format (:obj:`SimulationResultsFormat`): format to save the results of the simulation (e.g., `HDF5`)
    '''
    # check that model is encoded in SBML
    if model_sed_urn != "urn:sedml:language:sbml":
        raise NotImplementedError("Model language with URN '{}' is not supported".format(model_sed_urn))

    # check that simulation is a time course simulation
    if not isinstance(simulation, SteadyStateSimulation):
        raise NotImplementedError('{} is not supported'.format(simulation.__class__.__name__))

    # check that model parameter changes have already been applied (because handled by :obj:`exec_simulations_in_archive`)
    if simulation.model_parameter_changes:
        raise NotImplementedError('Model parameter changes are not supported')

    # check that the desired output format is supported
    if out_format != SimulationResultsFormat.HDF5:
        raise NotImplementedError("Simulation results format '{}' is not supported".format(out_format))

    # Read the model located at `os.path.join(working_dir, model_filename)` in the format
    # with the SED URN `model_sed_urn`.
    model = cobra.io.read_sbml_model(model_filename)

    # Load the algorithm specified by `simulation.algorithm`
    algorithm = KISAO_ALGORITHMS_PARAMETERS_MAP.get(simulation.algorithm.kisao_term.id, None)
    if algorithm is None:
        raise NotImplementedError(
            "Algorithm with KiSAO id '{}' is not supported".format(simulation.algorithm.kisao_term.id))

    # set up algorithm parameters specified by `simulation.algorithm_parameter_changes`
    args = dict(algorithm['default_args'])
    for parameter_change in simulation.algorithm_parameter_changes:
        parameter = algorithm['parameters'].get(parameter_change.parameter.kisao_term.id, None)
        if parameter is None:
            raise NotImplementedError(
                "Algorithm parameter with KiSAO id '{}' is not supported by {}".format(
                    parameter_change.parameter.kisao_term.id,
                    simulation.algorithm.kisao_term.id))

        param_value = parameter_change.value
        if 'parse_value' in parameter:
            param_value = parameter['parse_value'](param_value)

        if 'alg_arg' in parameter:
            args[parameter['alg_arg']] = param_value
        else:
            setattr(model, parameter['model_arg'], param_value)

    # execute algorithm
    solution = algorithm['method'](model, **args)

    # check that solution was optimal
    if solution.status != 'optimal':
        raise cobra.exceptions.OptimizationError("A solution could not be found. The solver status was '{}'.".format(
            solution.status))

    # Save a report of the results of the simulation with `simulation.num_time_points` time points
    # beginning at `simulation.output_start_time` to `out_filename` in `out_format` format.
    # This should save all of the variables specified by `simulation.model.variables`.
    vars = sorted(simulation.model.variables, key=lambda var: var.target)

    obj_targets = []
    rxn_targets = []
    species_targets = []
    obj_matrix = numpy.full((0, 1), numpy.nan)
    rxn_matrix = numpy.full((0, 2), numpy.nan)
    species_matrix = numpy.full((0, 1), numpy.nan)
    unpredicted_rxns = []
    unpredicted_species = []
    invalid_targets = []
    for var in vars:
        target = var.target
        obj_match = re.match(r"^/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective\[@fbc:id='(.*?)'\]$", target)
        rxn_match = re.match(r"^/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction\[@id='(.*?)'\]$", target)
        species_match = re.match(r"^/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species\[@id='(.*?)'\]$", target)

        if obj_match:
            obj_id = obj_match.group(1)
            i_target = len(obj_targets)
            obj_targets.append("[@fbc:id='{}']".format(obj_id))
            obj_matrix = numpy.concatenate((obj_matrix, numpy.full((1, obj_matrix.shape[1]), numpy.nan)), 0)
            obj_matrix[i_target, 0] = solution.objective_value
        elif rxn_match:
            rxn_id = rxn_match.group(1)
            value = solution.fluxes.get(rxn_id, numpy.nan)
            if numpy.isnan(value):
                unpredicted_rxns.append(rxn_id)
            else:
                i_target = len(rxn_targets)
                rxn_targets.append("[@id='{}']".format(rxn_id))
                rxn_matrix = numpy.concatenate((rxn_matrix, numpy.full((1, rxn_matrix.shape[1]), numpy.nan)), 0)
                rxn_matrix[i_target, 0] = value
                rxn_matrix[i_target, 1] = solution.reduced_costs.get(rxn_id)
        elif species_match:
            species_id = species_match.group(1)
            value = solution.shadow_prices.get(species_id, numpy.nan)
            if numpy.isnan(value):
                unpredicted_species.append(species_id)
            else:
                i_target = len(species_targets)
                species_targets.append("[@id='{}']".format(species_id))
                species_matrix = numpy.concatenate((species_matrix, numpy.full((1, species_matrix.shape[1]), numpy.nan)), 0)
                species_matrix[i_target, 0] = value
        else:
            invalid_targets.append(var.target)

    errors = []
    if len(obj_targets) > 1:
        errors.append('Only one objective could be predicted')
    if unpredicted_rxns:
        errors.append('Fluxes and reduced costs were not predicted for the following reactions:\n  - {}'.format(
            '\n  - '.join(sorted(unpredicted_rxns))))
    if unpredicted_species:
        errors.append('Shadow prices were not predicted for the following species:\n  - {}'.format(
            '\n  - '.join(sorted(unpredicted_species))))
    if invalid_targets:
        errors.append('The following targets were not predicted:\n  - {}'.format(
            '\n  - '.join(sorted(invalid_targets))))
    if errors:
        raise ValueError('\n\n'.join(errors))

    results = [
        {
            'path': "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective/@value",
            'axes': [
                {
                    'type': 'SIO_000921',
                    'labels': obj_targets
                }
            ],
            'value': obj_matrix
        },
        {
            'path': "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction/@flux",
            'axes': [
                {
                    'type': 'SIO_000921',
                    'labels': rxn_targets
                }
            ],
            'value': rxn_matrix[:, 0]
        },
        {
            'path': "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction/@reducedCost",
            'axes': [
                {
                    'type': 'SIO_000921',
                    'labels': rxn_targets
                }
            ],
            'value': rxn_matrix[:, 1]
        },
        {
            'path': "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species/@shadowPrice",
            'axes': [
                {
                    'type': 'SIO_000921',
                    'labels': species_targets
                }
            ],
            'value': species_matrix
        },
    ]

    Hdf5SimulationResultsWriter.run(results, out_filename)
