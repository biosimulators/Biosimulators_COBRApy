from biosimulators_cobrapy import data_model
import json
import os
import unittest


class DataModelTestCase(unittest.TestCase):

    def test_data_model_matches_specifications(self):
        with open(os.path.join(os.path.dirname(__file__), '..', 'biosimulators.json'), 'rb') as file:
            specs = json.load(file)

        self.assertEqual(
            set(data_model.KISAO_ALGORITHMS_PARAMETERS_MAP.keys()),
            set(alg_specs['kisaoId']['id'] for alg_specs in specs['algorithms']))

        for alg_specs in specs['algorithms']:
            alg_kisao_id = alg_specs['kisaoId']['id']
            params_props = data_model.KISAO_ALGORITHMS_PARAMETERS_MAP[alg_kisao_id]['parameters']
            self.assertEqual(
                set(params_props.keys()),
                set(param_specs['kisaoId']['id'] for param_specs in alg_specs['parameters']))

            for param_specs in alg_specs['parameters']:
                param_kisao_id = param_specs['kisaoId']['id']
                param_props = params_props[param_kisao_id]
                self.assertEqual(param_props['type'].value, param_specs['type'])
