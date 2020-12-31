from biosimulators_cobrapy.data_model import KISAO_ALGORITHMS_PARAMETERS_MAP
from biosimulators_cobrapy.utils import set_simulation_method_arg, validate_variables, get_results_of_variables
from biosimulators_utils.sedml.data_model import AlgorithmParameterChange, DataGeneratorVariable
from unittest import mock
import attrdict
import cobra
import numpy
import os
import unittest


class UtilsTestCase(unittest.TestCase):
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

        model['reactions'] = [
            attrdict.AttrDict(id='A'),
            attrdict.AttrDict(id='B'),
        ]
        argument_change = AlgorithmParameterChange(
            kisao_id='KISAO_0000534',
            new_value='["A", "B"]',
        )
        set_simulation_method_arg(method_props, argument_change, model, method_kw_args)
        self.assertEqual(model, {'solver': 'cplex', 'reactions': [{'id': 'A'}, {'id': 'B'}]})
        self.assertEqual(method_kw_args, {'loopless': False, 'fraction_of_optimum': 0.99, 'processes': 10, 'reaction_list': ['A', 'B']})

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

        # error: invalid reaction id
        argument_change = AlgorithmParameterChange(
            kisao_id='KISAO_0000534',
            new_value='["A", "B", "C"]',
        )
        with self.assertRaisesRegex(ValueError, 'not SBML ids of reactions'):
            set_simulation_method_arg(method_props, argument_change, model, method_kw_args)

    def test_validate_variables(self):
        method_props = KISAO_ALGORITHMS_PARAMETERS_MAP['KISAO_0000437']
        variables = [
            DataGeneratorVariable(target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']/@value"),
            DataGeneratorVariable(target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:type='maximize']/@value"),
            DataGeneratorVariable(target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']"),
            DataGeneratorVariable(target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective/@value"),
            DataGeneratorVariable(target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective"),
            DataGeneratorVariable(target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']/@flux"),
            DataGeneratorVariable(target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']/@reducedCost"),
            DataGeneratorVariable(target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@metaid='R_ACALD']/@flux"),
            DataGeneratorVariable(target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']"),
            DataGeneratorVariable(target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction/@flux"),
            DataGeneratorVariable(target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction"),
            DataGeneratorVariable(target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']/@shadowPrice"),
            DataGeneratorVariable(target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@metaid='M_13dpg_c']/@shadowPrice"),
            DataGeneratorVariable(target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']"),
            DataGeneratorVariable(target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species/@shadowPrice"),
            DataGeneratorVariable(target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species"),
        ]
        validate_variables(method_props, variables)

        variables = [
            DataGeneratorVariable(symbol='urn:sedml:symbol:time'),
        ]
        with self.assertRaises(NotImplementedError):
            validate_variables(method_props, variables)

        variables = [
            DataGeneratorVariable(target="/sbml:sbml/sbml:model/sbml:listOfCompartments/sbml:compartment[@id='c']")
        ]
        with self.assertRaises(ValueError):
            validate_variables(method_props, variables)

    def test_get_results_of_variables(self):
        method_props = KISAO_ALGORITHMS_PARAMETERS_MAP['KISAO_0000437']
        variables = [
            DataGeneratorVariable(id='obj',
                                  target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']/@value"),
            DataGeneratorVariable(id='R_ACALD_flux',
                                  target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']/@flux"),
            DataGeneratorVariable(id='R_ACALD_reduced_cost',
                                  target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']/@reducedCost"),
            DataGeneratorVariable(id='M_13dpg_c_shadow_price',
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
            variables[0].target: 'obj',
            variables[1].target: 'R_ACALD',
            variables[2].target: 'R_ACALD',
            variables[3].target: 'M_13dpg_c',
        }
        result = get_results_of_variables(method_props, variables, target_to_id, solution)
        self.assertEqual(set(result.keys()), set(var.id for var in variables))
        self.assertEqual(result['obj'], numpy.array(1.0))
        self.assertEqual(result['R_ACALD_flux'], numpy.array(2.0))
        self.assertEqual(result['R_ACALD_reduced_cost'], numpy.array(3.0))
        self.assertEqual(result['M_13dpg_c_shadow_price'], numpy.array(4.0))

        model_filename = os.path.join(os.path.dirname(__file__), 'fixtures', 'textbook.xml')
        model = cobra.io.read_sbml_model(model_filename)
        solution = model.optimize()
        result = get_results_of_variables(method_props, variables, target_to_id, solution)
