""" Methods for using COBRApy to execute SED tasks in COMBINE archives and save their outputs

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-31
:Copyright: 2020, BioSimulators Team
:License: MIT
"""

from biosimulators_utils.licensing.gurobi import GurobiLicenseManager
GurobiLicenseManager().save_keys_to_license_file()

from .data_model import KISAO_ALGORITHMS_PARAMETERS_MAP  # noqa: E402
from .utils import (get_objective_sbml_fbc_ids, set_simulation_method_arg,  # noqa: E402
                    apply_variables_to_simulation_method_args, validate_variables,
                    get_results_of_variables, get_results_paths_for_variables)
from biosimulators_utils.combine.exec import exec_sedml_docs_in_archive  # noqa: E402
from biosimulators_utils.config import get_config, Config  # noqa: F401, E402
from biosimulators_utils.log.data_model import CombineArchiveLog, TaskLog, StandardOutputErrorCapturerLevel  # noqa: F401, E402
from biosimulators_utils.model_lang.sbml.utils import get_package_namespace as get_sbml_package_namespace  # noqa: E402
from biosimulators_utils.viz.data_model import VizFormat  # noqa: F401, E402
from biosimulators_utils.report.data_model import ReportFormat, VariableResults, SedDocumentResults  # noqa: F401, E402
from biosimulators_utils.sedml import validation  # noqa: E402
from biosimulators_utils.sedml.data_model import (Task, ModelLanguage, ModelAttributeChange, SteadyStateSimulation,  # noqa: F401, E402
                                                  Variable)
from biosimulators_utils.sedml.exec import exec_sed_doc as base_exec_sed_doc  # noqa: E402
from biosimulators_utils.simulator.utils import get_algorithm_substitution_policy  # noqa: E402
from biosimulators_utils.utils.core import raise_errors_warnings  # noqa: E402
from biosimulators_utils.warnings import warn, BioSimulatorsWarning  # noqa: E402
from biosimulators_utils.xml.utils import get_namespaces_for_xml_doc  # noqa: E402
from kisao.data_model import AlgorithmSubstitutionPolicy, ALGORITHM_SUBSTITUTION_POLICY_LEVELS  # noqa: E402
from kisao.utils import get_preferred_substitute_algorithm_by_ids  # noqa: E402
from lxml import etree  # noqa: E402
import cobra.io  # noqa: E402
import copy  # noqa: E402
import os  # noqa: E402

__all__ = [
    'exec_sedml_docs_in_combine_archive',
    'exec_sed_doc',
    'exec_sed_task',
    'preprocess_sed_task',
]


def exec_sedml_docs_in_combine_archive(archive_filename, out_dir, config=None):
    """ Execute the SED tasks defined in a COMBINE/OMEX archive and save the outputs

    Args:
        archive_filename (:obj:`str`): path to COMBINE/OMEX archive
        out_dir (:obj:`str`): path to store the outputs of the archive

            * CSV: directory in which to save outputs to files
              ``{ out_dir }/{ relative-path-to-SED-ML-file-within-archive }/{ report.id }.csv``
            * HDF5: directory in which to save a single HDF5 file (``{ out_dir }/reports.h5``),
              with reports at keys ``{ relative-path-to-SED-ML-file-within-archive }/{ report.id }`` within the HDF5 file

        config (:obj:`Config`, optional): BioSimulators common configuration

    Returns:
        :obj:`tuple`:

            * :obj:`SedDocumentResults`: results
            * :obj:`CombineArchiveLog`: log
    """
    return exec_sedml_docs_in_archive(exec_sed_doc, archive_filename, out_dir,
                                      apply_xml_model_changes=True,
                                      config=config)


def exec_sed_doc(doc, working_dir, base_out_path, rel_out_path=None,
                 apply_xml_model_changes=True,
                 log=None, indent=0, pretty_print_modified_xml_models=False,
                 log_level=StandardOutputErrorCapturerLevel.c, config=None):
    """ Execute the tasks specified in a SED document and generate the specified outputs

    Args:
        doc (:obj:`SedDocument` or :obj:`str`): SED document or a path to SED-ML file which defines a SED document
        working_dir (:obj:`str`): working directory of the SED document (path relative to which models are located)

        base_out_path (:obj:`str`): path to store the outputs

            * CSV: directory in which to save outputs to files
              ``{base_out_path}/{rel_out_path}/{report.id}.csv``
            * HDF5: directory in which to save a single HDF5 file (``{base_out_path}/reports.h5``),
              with reports at keys ``{rel_out_path}/{report.id}`` within the HDF5 file

        rel_out_path (:obj:`str`, optional): path relative to :obj:`base_out_path` to store the outputs
        apply_xml_model_changes (:obj:`bool`, optional): if :obj:`True`, apply any model changes specified in the SED-ML file before
            calling :obj:`task_executer`.
        log (:obj:`SedDocumentLog`, optional): log of the document
        indent (:obj:`int`, optional): degree to indent status messages
        pretty_print_modified_xml_models (:obj:`bool`, optional): if :obj:`True`, pretty print modified XML models
        log_level (:obj:`StandardOutputErrorCapturerLevel`, optional): level at which to log output
        config (:obj:`Config`, optional): BioSimulators common configuration
        simulator_config (:obj:`SimulatorConfig`, optional): tellurium configuration

    Returns:
        :obj:`tuple`:

            * :obj:`ReportResults`: results of each report
            * :obj:`SedDocumentLog`: log of the document
    """
    return base_exec_sed_doc(exec_sed_task, doc, working_dir, base_out_path,
                             rel_out_path=rel_out_path,
                             apply_xml_model_changes=apply_xml_model_changes,
                             log=log,
                             indent=indent,
                             pretty_print_modified_xml_models=pretty_print_modified_xml_models,
                             log_level=log_level,
                             config=config)


def exec_sed_task(task, variables, preprocessed_task=None, log=None, config=None):
    ''' Execute a task and save its results

    Args:
        task (:obj:`Task`): task
        variables (:obj:`list` of :obj:`Variable`): variables that should be recorded
        preprocessed_task (:obj:`dict`, optional): preprocessed information about the task, including possible
            model changes and variables. This can be used to avoid repeatedly executing the same initialization
            for repeated calls to this method.
        log (:obj:`TaskLog`, optional): log for the task
        config (:obj:`Config`, optional): BioSimulators common configuration

    Returns:
        :obj:`tuple`:

            :obj:`VariableResults`: results of variables
            :obj:`TaskLog`: log

    Raises:
        :obj:`ValueError`: if the task or an aspect of the task is not valid, or the requested output variables
            could not be recorded
        :obj:`NotImplementedError`: if the task is not of a supported type or involves an unsuported feature
    '''
    config = config or get_config()

    if config.LOG and not log:
        log = TaskLog()

    if preprocessed_task is None:
        preprocessed_task = preprocess_sed_task(task, variables, config=config)

    # get model
    cobra_model = preprocessed_task['model']['model']

    # modify model
    if task.model.changes:
        raise_errors_warnings(validation.validate_model_change_types(task.model.changes, (ModelAttributeChange, )),
                              error_summary='Changes for model `{}` are not supported.'.format(task.model.id))

        model_change_obj_attr_map = preprocessed_task['model']['model_change_obj_attr_map']
        for change in task.model.changes:
            model_obj, attr_name = model_change_obj_attr_map[change.target]
            new_value = float(change.new_value)
            setattr(model_obj, attr_name, new_value)

    # Load the simulation method specified by ``sim.algorithm``
    method_props = preprocessed_task['simulation']['method_props']
    method_kw_args = copy.copy(preprocessed_task['simulation']['method_kw_args'])

    # encode variables into arguments of the simulation methods
    variable_xpath_sbml_id_map = preprocessed_task['model']['variable_xpath_sbml_id_map']
    apply_variables_to_simulation_method_args(variable_xpath_sbml_id_map, method_props, variables, method_kw_args)

    # execute simulation
    with GurobiLicenseManager():
        solution = method_props['method'](cobra_model, **method_kw_args)

        # check that solution was optimal
        if method_props['check_status'] and solution.status != 'optimal':
            raise cobra.exceptions.OptimizationError("A solution could not be found. The solver status was `{}`.".format(
                solution.status))

        if method_props['kisao_id'] in ['KISAO_0000527', 'KISAO_0000528']:
            solution.objective_value = cobra_model.optimize().objective_value

    # Get the results of each variable
    variable_results = get_results_of_variables(preprocessed_task['model']['variable_target_results_path_map'],
                                                variables, solution)

    # log action
    if config.LOG:
        log.algorithm = preprocessed_task['simulation']['algorithm_kisao_id']
        log.simulator_details = {
            'method': method_props['method'].__module__ + '.' + method_props['method'].__name__,
            'arguments': method_kw_args,
        }

    # Return the results of each variable and log
    return variable_results, log


def preprocess_sed_task(task, variables, config=None):
    """ Preprocess a SED task, including its possible model changes and variables. This is useful for avoiding
    repeatedly initializing tasks on repeated calls of :obj:`exec_sed_task`.

    Args:
        task (:obj:`Task`): task
        variables (:obj:`list` of :obj:`Variable`): variables that should be recorded
        config (:obj:`Config`, optional): BioSimulators common configuration

    Returns:
        :obj:`dict`: preprocessed information about the task
    """
    config = config or get_config()

    model = task.model
    sim = task.simulation

    # validate simulation
    if config.VALIDATE_SEDML:
        raise_errors_warnings(validation.validate_model_language(model.language, ModelLanguage.SBML),
                              error_summary='Language for model `{}` is not supported.'.format(model.id))
        raise_errors_warnings(validation.validate_model_change_types(model.changes, (ModelAttributeChange, )),
                              error_summary='Changes for model `{}` are not supported.'.format(model.id))
        raise_errors_warnings(validation.validate_simulation_type(sim, (SteadyStateSimulation, )),
                              error_summary='{} `{}` is not supported.'.format(sim.__class__.__name__, sim.id))

    # check model source exists
    if model.source and not os.path.isfile(model.source):
        raise FileNotFoundError('Model source `{}` is not a file.'.format(model.source))
    model_etree = etree.parse(model.source)
    namespaces = get_namespaces_for_xml_doc(model_etree)
    sbml_fbc_prefix, sbml_fbc_uri = get_sbml_package_namespace('fbc', namespaces)

    # Read the model
    cobra_model = cobra.io.read_sbml_model(model.source)

    # preprocess model changes
    model_change_sbml_id_map = validation.validate_target_xpaths(
        model.changes, model_etree, attr='id')
    model_change_obj_attr_map = {}
    sbml_id_model_obj_map = {'R_' + reaction.id: reaction for reaction in cobra_model.reactions}
    invalid_changes = []
    for change in model.changes:
        sbml_id = model_change_sbml_id_map[change.target]
        model_obj = sbml_id_model_obj_map.get(sbml_id, None)

        attr_name = None

        if model_obj is not None:
            _, _, attr = change.target.partition('/@')
            ns, _, attr = attr.partition(':')
            if change.target_namespaces.get(ns, None) == sbml_fbc_uri:
                if attr == 'lowerFluxBound':
                    attr_name = 'lower_bound'
                elif attr == 'upperFluxBound':
                    attr_name = 'upper_bound'

        if attr_name:
            model_change_obj_attr_map[change.target] = (model_obj, attr_name)
        else:
            invalid_changes.append(change.target)

    if invalid_changes:
        valid_changes = []
        for reaction in cobra_model.reactions:
            valid_changes.append(
                "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_{}']/@fbc:lowerFluxBound".format(reaction.id))
            valid_changes.append(
                "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_{}']/@fbc:upperFluxBound".format(reaction.id))

        msg = 'The following changes are invalid:\n  {}\n\nThe following targets are valid:\n  {}'.format(
            '\n  '.join(sorted(invalid_changes)),
            '\n  '.join(sorted(valid_changes)),
        )
        raise ValueError(msg)

    # preprocess variables
    variable_xpath_sbml_id_map = validation.validate_target_xpaths(
        variables, model_etree, attr='id')
    variable_xpath_sbml_fbc_id_map = validation.validate_target_xpaths(
        variables,
        model_etree,
        attr={
            'namespace': {
                'prefix': sbml_fbc_prefix,
                'uri': sbml_fbc_uri,
            },
            'name': 'id',
        }
    )

    # get the SBML-FBC id of the active objective
    active_objective_sbml_fbc_id, objective_sbml_fbc_ids = get_objective_sbml_fbc_ids(model.source)

    # Load the simulation method specified by ``sim.algorithm``
    algorithm_substitution_policy = get_algorithm_substitution_policy(config=config)
    exec_kisao_id = get_preferred_substitute_algorithm_by_ids(
        sim.algorithm.kisao_id, KISAO_ALGORITHMS_PARAMETERS_MAP.keys(),
        substitution_policy=algorithm_substitution_policy)
    method_props = KISAO_ALGORITHMS_PARAMETERS_MAP[exec_kisao_id]

    # set up method parameters specified by ``simulation.algorithm.changes``
    method_kw_args = {}
    if exec_kisao_id == sim.algorithm.kisao_id:
        for method_arg_change in sim.algorithm.changes:
            try:
                set_simulation_method_arg(method_props, method_arg_change, cobra_model, method_kw_args)
            except NotImplementedError as exception:
                if (
                    ALGORITHM_SUBSTITUTION_POLICY_LEVELS[algorithm_substitution_policy]
                    > ALGORITHM_SUBSTITUTION_POLICY_LEVELS[AlgorithmSubstitutionPolicy.NONE]
                ):
                    warn('Unsuported algorithm parameter `{}` was ignored:\n  {}'.format(
                        method_arg_change.kisao_id, str(exception).replace('\n', '\n  ')),
                        BioSimulatorsWarning)
                else:
                    raise
            except ValueError as exception:
                if (
                    ALGORITHM_SUBSTITUTION_POLICY_LEVELS[algorithm_substitution_policy]
                    > ALGORITHM_SUBSTITUTION_POLICY_LEVELS[AlgorithmSubstitutionPolicy.NONE]
                ):
                    warn('Unsuported value `{}` for algorithm parameter `{}` was ignored:\n  {}'.format(
                        method_arg_change.new_value, method_arg_change.kisao_id, str(exception).replace('\n', '\n  ')),
                        BioSimulatorsWarning)
                else:
                    raise

    solver_change = next((change for change in sim.algorithm.changes if change.kisao_id == 'KISAO_0000553'), None)
    if solver_change is None and GurobiLicenseManager().is_package_available():
        cobra_model.solver = 'gurobi'

    # validate variables
    validate_variables(cobra_model, active_objective_sbml_fbc_id, objective_sbml_fbc_ids,
                       method_props, variables, variable_xpath_sbml_id_map, variable_xpath_sbml_fbc_id_map,
                       sbml_fbc_uri)
    variable_target_results_path_map = get_results_paths_for_variables(cobra_model, active_objective_sbml_fbc_id, objective_sbml_fbc_ids,
                                                                       method_props, variables,
                                                                       variable_xpath_sbml_id_map, variable_xpath_sbml_fbc_id_map)

    # Return processed information about the task
    return {
        'model': {
            'model': cobra_model,
            'active_objective_sbml_fbc_id': active_objective_sbml_fbc_id,
            'model_change_obj_attr_map': model_change_obj_attr_map,
            'variable_target_results_path_map': variable_target_results_path_map,
            'variable_xpath_sbml_id_map': variable_xpath_sbml_id_map,
            'variable_xpath_sbml_fbc_id_map': variable_xpath_sbml_fbc_id_map,
        },
        'simulation': {
            'algorithm_kisao_id': exec_kisao_id,
            'method_props': method_props,
            'method_kw_args': method_kw_args,
        }
    }
