""" Utilities for working with COBRApy

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-31
:Copyright: 2020, BioSimulators Team
:License: MIT
"""

from biosimulators_utils.report.data_model import VariableResults
from biosimulators_utils.sedml.data_model import Variable  # noqa: F401
from biosimulators_utils.utils.core import validate_str_value, parse_value
import cobra  # noqa: F401
import libsbml
import numpy

__all__ = [
    'get_objective_sbml_fbc_ids',
    'set_simulation_method_arg',
    'apply_variables_to_simulation_method_args',
    'validate_variables',
    'get_results_paths_for_variables',
    'get_results_of_variables',
]


def get_objective_sbml_fbc_ids(model_source):
    """ Get the SBML-FBC id of the active objective

    Args:
        model_source (:obj:`str`): path to model

    Returns:
        :obj:`tuple`:

            * :obj:`str`: SBML-FBC id of the active objective
            * :obj:`list` of :obj:`str`: SBML-FBC id of the objectives
    """
    doc = libsbml.readSBMLFromFile(model_source)
    model = doc.getModel()
    model_fbc = model.getPlugin("fbc")
    return (
        model_fbc.getListOfObjectives().getActiveObjective(),
        [objective.getId() for objective in model_fbc.getListOfObjectives()],
    )


def set_simulation_method_arg(method_props, argument_change, model, model_method_kw_args):
    """ Set the value of an argument of a simulation method based on a SED
    algorithm parameter change

    Args:
        method_props (:obj:`dict`): properties of the simulation method
        argument_change (:obj:`AlgorithmParameterChange`): algorithm parameter change
        model (:obj:`cobra.core.model.Model`)
        model_method_kw_args (:obj:`dict`): keyword arguments for the simulation method
            for the model

    Raises:
        :obj:`NotImplementedError`: if the simulation method doesn't support the parameter
        :obj:`ValueError`: if the new value is not a valid value of the parameter
    """
    parameter_kisao_id = argument_change.kisao_id
    parameter = method_props['parameters'].get(parameter_kisao_id, None)
    if parameter is None:
        msg = "".join([
            "{} ({}) does not support parameter `{}`. ".format(
                method_props['name'], method_props['kisao_id'], argument_change.kisao_id),
            "The parameters of {} must have one of the following KiSAO ids:\n  - {}".format(
                method_props['name'],
                '\n  - '.join(
                    '{} ({}): {}'.format(kisao_id, parameter['name'], parameter['description'])
                    for kisao_id, parameter in method_props['parameters'].items())),
        ])
        raise NotImplementedError(msg)

    value = argument_change.new_value
    if not validate_str_value(value, parameter['type']):
        msg = "`{}` is not a valid value for parameter {} ({}) of {} ({})".format(
            value, parameter['name'], parameter_kisao_id,
            method_props['name'], method_props['kisao_id'])
        raise ValueError(msg)
    enum = parameter.get('enum', None)
    if enum:
        if value.lower() not in enum.__members__:
            msg = ("`{}` is not a valid value for parameter {} ({}) of {} ({}). "
                   "The value of {} must be one of the following:\n  - {}").format(
                value, parameter['name'], parameter_kisao_id,
                method_props['name'], method_props['kisao_id'],
                method_props['name'],
                '\n  - '.join(sorted('`' + value + '`' for value in enum.__members__.keys())))
            raise ValueError(msg)

    parsed_value = parse_value(value, parameter['type'])
    if enum:
        parsed_value = enum[value.lower()].value

    if 'alg_arg' in parameter:
        model_method_kw_args[parameter['alg_arg']] = parsed_value
    else:
        setattr(model, parameter['model_arg'], parsed_value)


def apply_variables_to_simulation_method_args(target_x_paths_ids, method_props, variables, model_method_kw_args):
    """ Encode the desired output variables into arguments to simulation methods

    Args:
        target_x_paths_ids (:obj:`dict` of :obj:`str` to :obj:`str`): dictionary that maps each XPath to the
            SBML id of the corresponding model object
        method_props (:obj:`dict`): properties of the simulation method
        variables (:obj:`list` of :obj:`Variable`): variables that should be recorded
        model_method_kw_args (:obj:`dict`): keyword arguments for the simulation method
            for the model
    """
    if method_props['kisao_id'] == 'KISAO_0000526':
        reaction_list = set()
        for variable in variables:
            reaction_id = target_x_paths_ids[variable.target]
            reaction_list.add(reaction_id[2:] if reaction_id.startswith('R_') else reaction_id)
        model_method_kw_args['reaction_list'] = sorted(reaction_list)


def validate_variables(model, active_objective_sbml_fbc_id, objective_sbml_fbc_ids,
                       method, variables, target_sbml_id_map, target_sbml_fbc_id_map, sbml_fbc_uri):
    """ Validate the desired output variables of a simulation

    Args:
        model (:obj:`cobra.core.model.Model`): model
        active_objective_sbml_fbc_id (:obj:`str`): SBML-FBC id of the active objective
        objective_sbml_fbc_ids (:obj:`list` of :obj:`str`): SBML-FBC id of the objectives
        method (:obj:`dict`): properties of desired simulation method
        variables (:obj:`list` of :obj:`Variable`): variables that should be recorded
        target_sbml_id_map (:obj:`dict` of :obj:`str` to :obj:`str`): dictionary that maps each XPath to the
            SBML id of the corresponding model object
        target_sbml_fbc_id_map (:obj:`dict` of :obj:`str` to :obj:`str`): dictionary that maps each XPath to the
            SBML-FBC id of the corresponding model object
        sbml_fbc_uri (:obj:`str`): URI for SBML FBC package
    """
    possible_target_results_path_map = set()
    for variable_pattern in method['variables']:
        for sbml_id, fbc_id, attr, result_type, result_name in variable_pattern['get_target_results_paths'](
                model, active_objective_sbml_fbc_id, objective_sbml_fbc_ids):
            possible_target_results_path_map.add((sbml_id, fbc_id, attr))

    invalid_symbols = set()
    invalid_targets = set()
    for variable in variables:
        if variable.symbol:
            invalid_symbols.add(variable.symbol)

        else:
            valid = True

            target = variable.target
            variable_target_id = target_sbml_id_map.get(target, None)
            variable_target_fbc_id = target_sbml_fbc_id_map.get(target, None)
            target_attr = target.partition('/@')[2] or None
            if target_attr:
                target_ns, _, target_attr = target_attr.rpartition(':')
                if target_ns and variable.target_namespaces.get(target_ns, None) != sbml_fbc_uri:
                    valid = False

            if not valid or (variable_target_id, variable_target_fbc_id, target_attr) not in possible_target_results_path_map:
                invalid_targets.add(variable.target)

    if invalid_symbols:
        raise NotImplementedError("{} ({}) doesn't support variables with symbols".format(
            method['name'], method['kisao_id']))

    if invalid_targets:
        msg = (
            "{} ({}) doesn't support variables with the following target XPaths:\n  - {}\n\n"
            "The targets of variables should match one of the following patterns of XPaths:\n  - {}"
        ).format(
            method['name'], method['kisao_id'],
            '\n  - '.join(sorted('`' + target + '`' for target in invalid_targets)),
            '\n  - '.join(sorted('{}: `{}`'.format(
                variable_pattern['description'], variable_pattern['target'])
                for variable_pattern in method['variables']))
        )
        raise ValueError(msg)


def get_results_paths_for_variables(model, active_objective_sbml_fbc_id, objective_sbml_fbc_ids,
                                    method, variables, target_sbml_id_map, target_sbml_fbc_id_map):
    """ Get the path to results for the desired variables

    Args:
        model (:obj:`cobra.core.model.Model`): model
        active_objective_sbml_fbc_id (:obj:`str`): SBML-FBC id of the active objective
        objective_sbml_fbc_ids (:obj:`list` of :obj:`str`): SBML-FBC id of the objectives
        method (:obj:`dict`): properties of desired simulation method
        variables (:obj:`list` of :obj:`Variable`): variables that should be recorded
        target_sbml_id_map (:obj:`dict` of :obj:`str` to :obj:`str`): dictionary that maps each XPath to the
            SBML id of the corresponding model object
        target_sbml_fbc_id_map (:obj:`dict` of :obj:`str` to :obj:`str`): dictionary that maps each XPath to the
            SBML-FBC id of the corresponding model object

    Returns:
        :obj:`dict`: path to results of desired variables
    """
    possible_target_results_path_map = {}
    for variable_pattern in method['variables']:
        for sbml_id, fbc_id, attr, result_type, result_name in variable_pattern['get_target_results_paths'](
                model, active_objective_sbml_fbc_id, objective_sbml_fbc_ids):
            possible_target_results_path_map[(sbml_id, fbc_id, attr)] = (result_type, result_name)

    target_results_path_map = {}
    for variable in variables:
        target = variable.target
        variable_target_id = target_sbml_id_map[target]
        variable_target_fbc_id = target_sbml_fbc_id_map[target]
        target_attr = target.partition('/@')[2].rpartition(':')[2] or None
        target_results_path_map[variable.target] = possible_target_results_path_map[(
            variable_target_id, variable_target_fbc_id, target_attr)]

    return target_results_path_map


def get_results_of_variables(target_results_path_map, variables, solution):
    """ Get the results of the desired variables

    Args:
        target_results_path_map (:obj:`dict`): path to results of desired variables
        variables (:obj:`list` of :obj:`Variable`): variables that should be recorded
        solution (:obj:`cobra.core.solution.Solution`): solution of method

    Returns:
        :obj:`VariableResults`: the results of desired variables
    """
    variable_results = VariableResults()
    for variable in variables:
        result_type, result_name = target_results_path_map[variable.target]
        if result_type:
            result = getattr(solution, result_type)
            if result_name:
                if hasattr(result, 'get'):
                    result = result.get(*result_name)
                else:
                    result = result[result_name]
        else:
            result = numpy.nan

        variable_results[variable.id] = numpy.array(result)

    return variable_results
