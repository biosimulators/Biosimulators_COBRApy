from biosimulators_cobrapy.data_model import KISAO_ALGORITHMS_PARAMETERS_MAP
from biosimulators_cobrapy.utils import (get_active_objective_sbml_fbc_id, set_simulation_method_arg,
                                         apply_variables_to_simulation_method_args,
                                         validate_variables, get_results_of_variables)
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

    def test_get_active_objective_sbml_fbc_id(self):
        self.assertEqual(get_active_objective_sbml_fbc_id(self.MODEL_FILENAME), 'obj')

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
        method_props = KISAO_ALGORITHMS_PARAMETERS_MAP['KISAO_0000526']
        variables = [
            Variable(target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_A']/@minFlux"),
            Variable(target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_A']/@maxFlux"),
            Variable(target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_B']/@minFlux"),
            Variable(target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_C']/@maxFlux"),
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
        method_props = KISAO_ALGORITHMS_PARAMETERS_MAP['KISAO_0000437']
        variables = [
            Variable(target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']/@value"),
            Variable(target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:type='maximize']/@value"),
            Variable(target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']"),
            Variable(target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective/@value"),
            Variable(target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective"),
            Variable(target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']/@flux"),
            Variable(target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']/@reducedCost"),
            Variable(target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@metaid='R_ACALD']/@flux"),
            Variable(target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']"),
            Variable(target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction/@flux"),
            Variable(target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction"),
            Variable(target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']/@shadowPrice"),
            Variable(target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@metaid='M_13dpg_c']/@shadowPrice"),
            Variable(target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']"),
            Variable(target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species/@shadowPrice"),
            Variable(target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species"),
        ]
        validate_variables(method_props, variables)

        variables = [
            Variable(symbol='urn:sedml:symbol:time'),
        ]
        with self.assertRaises(NotImplementedError):
            validate_variables(method_props, variables)

        variables = [
            Variable(target="/sbml:sbml/sbml:model/sbml:listOfCompartments/sbml:compartment[@id='c']")
        ]
        with self.assertRaises(ValueError):
            validate_variables(method_props, variables)

    def test_get_results_of_variables(self):
        method_props = KISAO_ALGORITHMS_PARAMETERS_MAP['KISAO_0000437']
        variables = [
            Variable(id='obj',
                                  target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']/@value"),
            Variable(id='inactive_obj',
                                  target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='inactive_obj']/@value"),
            Variable(id='R_ACALD_flux',
                                  target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']/@flux"),
            Variable(id='R_ACALD_reduced_cost',
                                  target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']/@reducedCost"),
            Variable(id='M_13dpg_c_shadow_price',
                                  target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']/@shadowPrice"),
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
        result = get_results_of_variables(target_to_id, target_to_fbc_id, 'obj', method_props, variables, solution)
        self.assertEqual(set(result.keys()), set(var.id for var in variables))
        numpy.testing.assert_allclose(result['obj'], numpy.array(1.0))
        numpy.testing.assert_allclose(result['inactive_obj'], numpy.array(numpy.nan))
        numpy.testing.assert_allclose(result['R_ACALD_flux'], numpy.array(2.0))
        numpy.testing.assert_allclose(result['R_ACALD_reduced_cost'], numpy.array(3.0))
        numpy.testing.assert_allclose(result['M_13dpg_c_shadow_price'], numpy.array(4.0))

        model = cobra.io.read_sbml_model(self.MODEL_FILENAME)
        solution = model.optimize()
        result = get_results_of_variables(target_to_id, target_to_fbc_id, 'obj', method_props, variables, solution)
