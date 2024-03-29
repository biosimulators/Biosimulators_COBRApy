from biosimulators_cobrapy.data_model import KISAO_ALGORITHMS_PARAMETERS_MAP
from biosimulators_cobrapy.utils import (get_objective_sbml_fbc_ids, set_simulation_method_arg,
                                         apply_variables_to_simulation_method_args,
                                         validate_variables, get_results_of_variables, get_results_paths_for_variables)
from biosimulators_utils.sedml.data_model import AlgorithmParameterChange, Variable
from unittest import mock
import attrdict
import cobra
import numpy
import numpy.testing
import os
import unittest


class UtilsTestCase(unittest.TestCase):
    MODEL_FILENAME = os.path.join(os.path.dirname(__file__), 'fixtures', 'textbook.xml')

    def test_get_objective_sbml_fbc_ids(self):
        self.assertEqual(get_objective_sbml_fbc_ids(self.MODEL_FILENAME), ('obj', ['obj', 'inactive_obj']))

    def test_set_simulation_method_arg(self):
        method_props = KISAO_ALGORITHMS_PARAMETERS_MAP['KISAO_0000526']
        model = attrdict.AttrDict()
        method_kw_args = {}

        argument_change = AlgorithmParameterChange(
            kisao_id='KISAO_0000532',
            new_value='true',
        )
        set_simulation_method_arg(method_props, argument_change, model, method_kw_args)
        self.assertEqual(model, {})
        self.assertEqual(method_kw_args, {'loopless': True})

        argument_change = AlgorithmParameterChange(
            kisao_id='KISAO_0000532',
            new_value='0',
        )
        set_simulation_method_arg(method_props, argument_change, model, method_kw_args)
        self.assertEqual(model, {})
        self.assertEqual(method_kw_args, {'loopless': False})

        argument_change = AlgorithmParameterChange(
            kisao_id='KISAO_0000531',
            new_value='0.99',
        )
        set_simulation_method_arg(method_props, argument_change, model, method_kw_args)
        self.assertEqual(model, {})
        self.assertEqual(method_kw_args, {'loopless': False, 'fraction_of_optimum': 0.99})

        argument_change = AlgorithmParameterChange(
            kisao_id='KISAO_0000529',
            new_value='10',
        )
        set_simulation_method_arg(method_props, argument_change, model, method_kw_args)
        self.assertEqual(model, {})
        self.assertEqual(method_kw_args, {'loopless': False, 'fraction_of_optimum': 0.99, 'processes': 10})

        argument_change = AlgorithmParameterChange(
            kisao_id='KISAO_0000553',
            new_value='CPLEX',
        )
        set_simulation_method_arg(method_props, argument_change, model, method_kw_args)
        self.assertEqual(model, {'solver': 'cplex'})
        self.assertEqual(method_kw_args, {'loopless': False, 'fraction_of_optimum': 0.99, 'processes': 10})

        # error: unsupported parameter
        argument_change = AlgorithmParameterChange(
            kisao_id='KISAO_0000000',
            new_value='true',
        )
        with self.assertRaisesRegex(NotImplementedError, 'does not support parameter'):
            set_simulation_method_arg(method_props, argument_change, model, method_kw_args)

        # error: invalid value
        argument_change = AlgorithmParameterChange(
            kisao_id='KISAO_0000531',
            new_value='A',
        )
        with self.assertRaisesRegex(ValueError, 'not a valid value'):
            set_simulation_method_arg(method_props, argument_change, model, method_kw_args)

        # error: invalid value of enumeration
        argument_change = AlgorithmParameterChange(
            kisao_id='KISAO_0000553',
            new_value='unknown',
        )
        with self.assertRaisesRegex(ValueError, 'not a valid value'):
            set_simulation_method_arg(method_props, argument_change, model, method_kw_args)

    def test_apply_variables_to_simulation_method_args(self):
        ns = {
            'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
        }
        method_props = KISAO_ALGORITHMS_PARAMETERS_MAP['KISAO_0000526']
        variables = [
            Variable(target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_A']/@minFlux", target_namespaces=ns),
            Variable(target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_A']/@maxFlux", target_namespaces=ns),
            Variable(target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_B']/@minFlux", target_namespaces=ns),
            Variable(target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_C']/@maxFlux", target_namespaces=ns),
        ]
        target_x_paths_ids = {
            variables[0].target: 'R_A',
            variables[1].target: 'R_A',
            variables[2].target: 'R_B',
            variables[3].target: 'R_C',
        }

        # FVA
        module_method_args = {}
        expected_module_method_args = {'reaction_list': ['A', 'B', 'C']}
        apply_variables_to_simulation_method_args(target_x_paths_ids, method_props, variables, module_method_args)
        self.assertEqual(module_method_args, expected_module_method_args)

        # FBA
        method_props = KISAO_ALGORITHMS_PARAMETERS_MAP['KISAO_0000437']
        module_method_args = {}
        expected_module_method_args = {}
        apply_variables_to_simulation_method_args(target_x_paths_ids, method_props, variables, module_method_args)
        self.assertEqual(module_method_args, expected_module_method_args)

    def test_validate_variables(self):
        ns = {
            'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
            'fbc': 'http://www.sbml.org/sbml/level3/version1/fbc/version2',
        }
        model = cobra.io.read_sbml_model(self.MODEL_FILENAME)
        active_objective_sbml_fbc_id = 'obj'
        objective_sbml_fbc_ids = ['obj', 'inactive_obj']
        target_sbml_id_map = {
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']/@value": None,
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:type='maximize']/@value": None,
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']": None,
            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']/@flux": 'R_ACALD',
            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']/@reducedCost": 'R_ACALD',
            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@metaid='R_ACALD']/@flux": 'R_ACALD',
            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']": 'R_ACALD',
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']/@shadowPrice": 'M_13dpg_c',
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@metaid='M_13dpg_c']/@shadowPrice": 'M_13dpg_c',
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']": 'M_13dpg_c',
        }
        target_sbml_fbc_id_map = {
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']/@value": 'obj',
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:type='maximize']/@value": 'obj',
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']": 'obj',
            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']/@flux": None,
            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']/@reducedCost": None,
            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@metaid='R_ACALD']/@flux": None,
            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']": None,
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']/@shadowPrice": None,
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@metaid='M_13dpg_c']/@shadowPrice": None,
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']": None,
        }
        sbml_fbc_uri = ns['fbc']
        method_props = KISAO_ALGORITHMS_PARAMETERS_MAP['KISAO_0000437']
        variables = [
            Variable(target_namespaces=ns, target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']/@value"),
            Variable(target_namespaces=ns, target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:type='maximize']/@value"),
            Variable(target_namespaces=ns, target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']"),
            Variable(target_namespaces=ns, target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']/@flux"),
            Variable(target_namespaces=ns, target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']/@reducedCost"),
            Variable(target_namespaces=ns, target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@metaid='R_ACALD']/@flux"),
            Variable(target_namespaces=ns, target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']"),
            Variable(target_namespaces=ns, target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']/@shadowPrice"),
            Variable(target_namespaces=ns,
                     target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@metaid='M_13dpg_c']/@shadowPrice"),
            Variable(target_namespaces=ns, target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']"),
        ]
        validate_variables(model, active_objective_sbml_fbc_id, objective_sbml_fbc_ids,
                           method_props, variables, target_sbml_id_map, target_sbml_fbc_id_map, sbml_fbc_uri)

        variables = [
            Variable(symbol='urn:sedml:symbol:time'),
        ]
        with self.assertRaises(NotImplementedError):
            validate_variables(model, active_objective_sbml_fbc_id, objective_sbml_fbc_ids,
                               method_props, variables, target_sbml_id_map, target_sbml_fbc_id_map, sbml_fbc_uri)

        variables = [
            Variable(target_namespaces=ns, target="/sbml:sbml/sbml:model/sbml:listOfCompartments/sbml:compartment[@id='c']")
        ]
        with self.assertRaises(ValueError):
            validate_variables(model, active_objective_sbml_fbc_id, objective_sbml_fbc_ids,
                               method_props, variables, target_sbml_id_map, target_sbml_fbc_id_map, sbml_fbc_uri)

        variables = [
            Variable(target_namespaces=ns, target="/sbml:sbml/sbml:model/sbml:listOfCompartments/sbml:compartment[@id='c']/@sbml:id")
        ]
        with self.assertRaises(ValueError):
            validate_variables(model, active_objective_sbml_fbc_id, objective_sbml_fbc_ids,
                               method_props, variables, target_sbml_id_map, target_sbml_fbc_id_map, sbml_fbc_uri)

    def test_get_results_of_variables(self):
        ns = {
            'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
            'fbc': 'http://www.sbml.org/sbml/level3/version1/fbc/version2',
        }
        method_props = KISAO_ALGORITHMS_PARAMETERS_MAP['KISAO_0000437']
        variables = [
            Variable(
                id='obj',
                target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']/@value",
                target_namespaces=ns,
            ),
            Variable(
                id='inactive_obj',
                target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='inactive_obj']/@value",
                target_namespaces=ns,
            ),
            Variable(
                id='R_ACALD_flux',
                target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']/@flux",
                target_namespaces=ns,
            ),
            Variable(
                id='R_ACALD_reduced_cost',
                target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']/@reducedCost",
                target_namespaces=ns,
            ),
            Variable(
                id='M_13dpg_c_shadow_price',
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']/@shadowPrice",
                target_namespaces=ns,
            ),
        ]

        solution = mock.Mock(
            objective_value=1.0,
            fluxes=mock.Mock(
                get=lambda id: 2.0,
            ),
            reduced_costs=mock.Mock(
                get=lambda id: 3.0,
            ),
            shadow_prices=mock.Mock(
                get=lambda id: 4.0,
            ),
        )

        target_to_id = {
            variables[0].target: None,
            variables[1].target: None,
            variables[2].target: 'R_ACALD',
            variables[3].target: 'R_ACALD',
            variables[4].target: 'M_13dpg_c',
        }
        target_to_fbc_id = {
            variables[0].target: 'obj',
            variables[1].target: 'inactive_obj',
            variables[2].target: None,
            variables[3].target: None,
            variables[4].target: None,
        }
        model = cobra.io.read_sbml_model(self.MODEL_FILENAME)
        target_results_path_map = get_results_paths_for_variables(
            model, 'obj', ['obj', 'inactive_obj'], method_props, variables, target_to_id, target_to_fbc_id)
        result = get_results_of_variables(target_results_path_map, variables, solution)
        self.assertEqual(set(result.keys()), set(var.id for var in variables))
        numpy.testing.assert_allclose(result['obj'], numpy.array(1.0))
        numpy.testing.assert_allclose(result['inactive_obj'], numpy.array(numpy.nan))
        numpy.testing.assert_allclose(result['R_ACALD_flux'], numpy.array(2.0))
        numpy.testing.assert_allclose(result['R_ACALD_reduced_cost'], numpy.array(3.0))
        numpy.testing.assert_allclose(result['M_13dpg_c_shadow_price'], numpy.array(4.0))

        solution = model.optimize()
        target_results_path_map = get_results_paths_for_variables(
            model, 'obj', ['obj', 'inactive_obj'], method_props, variables, target_to_id, target_to_fbc_id)
        result = get_results_of_variables(target_results_path_map, variables, solution)
