""" Tests of the command-line interface

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-10-29
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from biosimulators_cobrapy import __main__
from biosimulators_cobrapy import core
from biosimulators_utils.combine import data_model as combine_data_model
from biosimulators_utils.combine.exceptions import CombineArchiveExecutionError
from biosimulators_utils.combine.io import CombineArchiveWriter
from biosimulators_utils.report import data_model as report_data_model
from biosimulators_utils.report.io import ReportReader
from biosimulators_utils.simulator.exec import exec_sedml_docs_in_archive_with_containerized_simulator
from biosimulators_utils.simulator.specs import gen_algorithms_from_specs
from biosimulators_utils.sedml import data_model as sedml_data_model
from biosimulators_utils.sedml.io import SedmlSimulationWriter
from biosimulators_utils.sedml.utils import append_all_nested_children_to_doc
from biosimulators_utils.warnings import BioSimulatorsWarning
from kisao.exceptions import AlgorithmCannotBeSubstitutedException
from unittest import mock
import cobra
import datetime
import dateutil.tz
import numpy
import numpy.testing
import os
import shutil
import tempfile
import unittest


class CliTestCase(unittest.TestCase):
    DOCKER_IMAGE = 'ghcr.io/biosimulators/biosimulators_cobrapy/cobrapy:latest'
    NAMESPACES = {
        'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
        'fbc': 'http://www.sbml.org/sbml/level3/version1/fbc/version2',
    }

    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_exec_sed_task_successfully(self):
        task = sedml_data_model.Task(
            model=sedml_data_model.Model(
                source=os.path.join(os.path.dirname(__file__), 'fixtures', 'textbook.xml'),
                language=sedml_data_model.ModelLanguage.SBML.value,
            ),
            simulation=sedml_data_model.SteadyStateSimulation(
                algorithm=sedml_data_model.Algorithm(
                    kisao_id='KISAO_0000437',
                    changes=[
                        sedml_data_model.AlgorithmParameterChange(
                            kisao_id='KISAO_0000553',
                            new_value='GLPK',
                        ),
                    ],
                ),
            ),
        )

        variables = [
            sedml_data_model.Variable(
                id='ACONTa_flux',
                target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACONTa']/@flux",
                target_namespaces=self.NAMESPACES,
                task=task),
            sedml_data_model.Variable(
                id='TALA_flux',
                target='/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id="R_TALA"]',
                target_namespaces=self.NAMESPACES,
                task=task),
            sedml_data_model.Variable(
                id='ACALD_costs',
                target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']/@reducedCost",
                target_namespaces=self.NAMESPACES,
                task=task),
            sedml_data_model.Variable(
                id='THD2_cost',
                target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_THD2']/@reducedCost",
                target_namespaces=self.NAMESPACES,
                task=task),
            sedml_data_model.Variable(
                id='13dpg_c_price',
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']/@shadowPrice",
                target_namespaces=self.NAMESPACES,
                task=task),
            sedml_data_model.Variable(
                id='succ_c_price',
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_succ_c']",
                target_namespaces=self.NAMESPACES,
                task=task),
            sedml_data_model.Variable(
                id='active_objective',
                target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']/@value",
                target_namespaces=self.NAMESPACES,
                task=task),
            sedml_data_model.Variable(
                id='inactive_objective',
                target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='inactive_obj']/@value",
                target_namespaces=self.NAMESPACES,
                task=task),
        ]

        # FBA
        variable_results, _ = core.exec_sed_task(task, variables)

        expected_results = {
            'ACONTa_flux': 6.007250,
            'TALA_flux': 1.496984,
            'ACALD_costs': 6.938894e-18,
            'THD2_cost': -2.546243e-03,
            '13dpg_c_price': -0.047105,
            'succ_c_price': -0.050925,
            'active_objective': 0.8739215069684301,
            'inactive_objective': numpy.nan,
        }

        self.assertTrue(set(variable_results.keys()), set(expected_results.keys()))

        for var_id, result in variable_results.items():
            numpy.testing.assert_allclose(result, numpy.array(expected_results[var_id]), rtol=1e-4, atol=1e-8)

        # pFBA
        task.simulation.algorithm.kisao_id = 'KISAO_0000528'
        variable_results, _ = core.exec_sed_task(task, variables)

        expected_results = {
            'ACONTa_flux': 6.007250e+00,
            'TALA_flux': 1.496984e+00,
            'ACALD_costs': -2.000000,
            'THD2_cost': 3.822222,
            '13dpg_c_price': 18.911111,
            'succ_c_price': 9.844444,
            'active_objective': 0.8739215069684301,
            'inactive_objective': numpy.nan,
        }

        self.assertTrue(set(variable_results.keys()), set(expected_results.keys()))

        for var_id, result in variable_results.items():
            numpy.testing.assert_allclose(result, numpy.array(expected_results[var_id]), rtol=1e-4, atol=1e-8)

        # pFBA
        task.simulation.algorithm.kisao_id = 'KISAO_0000527'
        variable_results, _ = core.exec_sed_task(task, variables)

        expected_results = {
            'ACONTa_flux': 6.007250e+00,
            'TALA_flux': 1.496984e+00,
            'ACALD_costs': numpy.nan,
            'THD2_cost': numpy.nan,
            '13dpg_c_price': numpy.nan,
            'succ_c_price': numpy.nan,
            'active_objective': 0.8739215069684301,
            'inactive_objective': numpy.nan,
        }

        self.assertTrue(set(variable_results.keys()), set(expected_results.keys()))

        for var_id, result in variable_results.items():
            numpy.testing.assert_allclose(result, numpy.array(expected_results[var_id]), rtol=1e-4, atol=1e-8)

        # FVA
        task.simulation.algorithm.kisao_id = 'KISAO_0000526'
        variables = [
            sedml_data_model.Variable(
                id='ACONTa_min_flux',
                target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACONTa']/@minFlux",
                target_namespaces=self.NAMESPACES,
                task=task),
            sedml_data_model.Variable(
                id='ACONTa_max_flux',
                target='/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id="R_ACONTa"]/@maxFlux',
                target_namespaces=self.NAMESPACES,
                task=task),
            sedml_data_model.Variable(
                id='SUCDi_min_flux',
                target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_SUCDi']/@minFlux",
                target_namespaces=self.NAMESPACES,
                task=task),
            sedml_data_model.Variable(
                id='SUCDi_max_flux',
                target='/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id="R_SUCDi"]/@maxFlux',
                target_namespaces=self.NAMESPACES,
                task=task),
        ]
        variable_results, _ = core.exec_sed_task(task, variables)

        expected_results = {
            'ACONTa_min_flux': 6.007250e+00,
            'ACONTa_max_flux': 6.007250e+00,
            'SUCDi_min_flux': 5.064376e+00,
            'SUCDi_max_flux': 1e3,
        }

        self.assertTrue(set(variable_results.keys()), set(expected_results.keys()))

        for var_id, result in variable_results.items():
            numpy.testing.assert_allclose(result, numpy.array(expected_results[var_id]), rtol=1e-4, atol=1e-8)

    def test_exec_sed_task_error_handling(self):
        # unsupported algorithm
        with self.assertRaisesRegex(ValueError, 'invalid KiSAO id'):
            self._build_combine_archive(algorithm=sedml_data_model.Algorithm(kisao_id='KISAO_0000001'))

        _, archive_filename = self._build_combine_archive(algorithm=sedml_data_model.Algorithm(kisao_id='KISAO_0000448'))
        with self.assertRaisesRegex(CombineArchiveExecutionError, 'No algorithm can be substituted'):
            core.exec_sedml_docs_in_combine_archive(archive_filename, self.dirname)

        _, archive_filename = self._build_combine_archive(
            algorithm=sedml_data_model.Algorithm(
                kisao_id='KISAO_0000437',
                changes=[sedml_data_model.AlgorithmParameterChange(kisao_id='KISAO_0000553', new_value='GLPK2')]
            ))
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'NONE'}):
            with self.assertRaisesRegex(CombineArchiveExecutionError, 'is not a valid'):
                core.exec_sedml_docs_in_combine_archive(archive_filename, self.dirname)

        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'SIMILAR_VARIABLES'}):
            with self.assertWarnsRegex(BioSimulatorsWarning, 'Unsuported value'):
                core.exec_sedml_docs_in_combine_archive(archive_filename, self.dirname)

        _, archive_filename = self._build_combine_archive(
            algorithm=sedml_data_model.Algorithm(
                kisao_id='KISAO_0000528',
                changes=[sedml_data_model.AlgorithmParameterChange(kisao_id='KISAO_0000531', new_value='not a number')]
            ))
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'NONE'}):
            with self.assertRaisesRegex(CombineArchiveExecutionError, 'not a valid value'):
                core.exec_sedml_docs_in_combine_archive(archive_filename, self.dirname)

        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'SIMILAR_VARIABLES'}):
            with self.assertWarnsRegex(BioSimulatorsWarning, 'Unsuported value'):
                core.exec_sedml_docs_in_combine_archive(archive_filename, self.dirname)

        _, archive_filename = self._build_combine_archive(
            algorithm=sedml_data_model.Algorithm(
                kisao_id='KISAO_0000528',
                changes=[sedml_data_model.AlgorithmParameterChange(kisao_id='KISAO_0000211', new_value='not a number')]
            ))
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'NONE'}):
            with self.assertRaisesRegex(CombineArchiveExecutionError, 'does not support parameter'):
                core.exec_sedml_docs_in_combine_archive(archive_filename, self.dirname)

        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'SIMILAR_VARIABLES'}):
            with self.assertWarnsRegex(BioSimulatorsWarning, 'does not support parameter'):
                core.exec_sedml_docs_in_combine_archive(archive_filename, self.dirname)

        # no solution
        model_changes = [
            sedml_data_model.ModelAttributeChange(
                target="/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='R_EX_glc__D_e_lower_bound']/@value",
                target_namespaces=self.NAMESPACES,
                new_value="10",
            ),
        ]
        _, archive_filename = self._build_combine_archive(model_changes=model_changes)
        with self.assertRaisesRegex(CombineArchiveExecutionError, 'could not be found'):
            core.exec_sedml_docs_in_combine_archive(archive_filename, self.dirname)

    def test_exec_sedml_docs_in_combine_archive_successfully(self):
        doc, archive_filename = self._build_combine_archive()

        out_dir = os.path.join(self.dirname, 'out')
        core.exec_sedml_docs_in_combine_archive(archive_filename, out_dir,
                                                report_formats=[
                                                    report_data_model.ReportFormat.h5,
                                                ],
                                                bundle_outputs=True,
                                                keep_individual_outputs=True)

        self._assert_combine_archive_outputs(doc, out_dir)

    def _build_combine_archive(self, model_changes=None, algorithm=None):
        doc = self._build_sed_doc(model_changes=model_changes, algorithm=algorithm)

        archive_dirname = os.path.join(self.dirname, 'archive')
        if not os.path.isdir(archive_dirname):
            os.mkdir(archive_dirname)

        model_filename = os.path.join(archive_dirname, 'model_1.xml')
        shutil.copyfile(
            os.path.join(os.path.dirname(__file__), 'fixtures', 'textbook.xml'),
            model_filename)

        sim_filename = os.path.join(archive_dirname, 'sim_1.sedml')
        SedmlSimulationWriter().run(doc, sim_filename)

        updated = datetime.datetime(2020, 1, 2, 1, 2, 3, tzinfo=dateutil.tz.tzutc())
        archive = combine_data_model.CombineArchive(
            contents=[
                combine_data_model.CombineArchiveContent(
                    'model_1.xml', combine_data_model.CombineArchiveContentFormat.SBML.value, updated=updated),
                combine_data_model.CombineArchiveContent(
                    'sim_1.sedml', combine_data_model.CombineArchiveContentFormat.SED_ML.value, updated=updated),
            ],
            updated=updated,
        )
        archive_filename = os.path.join(self.dirname,
                                        'archive.omex' if algorithm is None else 'archive-{}.omex'.format(algorithm.kisao_id))
        CombineArchiveWriter().run(archive, archive_dirname, archive_filename)

        return (doc, archive_filename)

    def _build_sed_doc(self, model_changes=None, algorithm=None):
        model_changes = (model_changes or []) + [
            sedml_data_model.ModelAttributeChange(
                target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACONTa']/@id",
                target_namespaces=self.NAMESPACES,
                new_value="ACONTa"
            ),
            sedml_data_model.ModelAttributeChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']/@id",
                target_namespaces=self.NAMESPACES,
                new_value="13dpg_c"
            ),
            sedml_data_model.ModelAttributeChange(
                target=("/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_GAPD']"
                        "/sbml:listOfProducts/sbml:speciesReference[@species='M_13dpg_c']/@species"),
                target_namespaces=self.NAMESPACES,
                new_value="13dpg_c"
            ),
            sedml_data_model.ModelAttributeChange(
                target=("/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_PGK']"
                        "/sbml:listOfProducts/sbml:speciesReference[@species='M_13dpg_c']/@species"),
                target_namespaces=self.NAMESPACES,
                new_value="13dpg_c"
            ),
        ]

        if algorithm is None:
            algorithm = sedml_data_model.Algorithm(
                kisao_id='KISAO_0000437',
                changes=[
                    sedml_data_model.AlgorithmParameterChange(
                        kisao_id='KISAO_0000553',
                        new_value='GLPK',
                    ),
                ],
            )

        doc = sedml_data_model.SedDocument()
        doc.models.append(sedml_data_model.Model(
            id='model_1',
            source='model_1.xml',
            language=sedml_data_model.ModelLanguage.SBML.value,
            changes=model_changes,
        ))
        doc.simulations.append(sedml_data_model.SteadyStateSimulation(
            id='sim_1_time_course',
            algorithm=algorithm,
        ))
        doc.tasks.append(sedml_data_model.Task(
            id='task_1',
            model=doc.models[0],
            simulation=doc.simulations[0],
        ))

        if algorithm.kisao_id in ['KISAO_0000437', 'KISAO_0000528', 'KISAO_0000527']:
            doc.data_generators.append(sedml_data_model.DataGenerator(
                id='data_gen_ACONTa_flux',
                variables=[
                    sedml_data_model.Variable(
                        id='var_ACONTa_flux',
                        target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='ACONTa']/@flux",
                        target_namespaces=self.NAMESPACES,
                        task=doc.tasks[0],
                    ),
                ],
                math='var_ACONTa_flux',
            ))
            doc.data_generators.append(sedml_data_model.DataGenerator(
                id='data_gen_TALA_flux',
                variables=[
                    sedml_data_model.Variable(
                        id='var_TALA_flux',
                        target='/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id="R_TALA"]',
                        target_namespaces=self.NAMESPACES,
                        task=doc.tasks[0],
                    ),
                ],
                math='var_TALA_flux',
            ))
            doc.data_generators.append(sedml_data_model.DataGenerator(
                id='data_gen_ACALD_reduced_cost',
                variables=[
                    sedml_data_model.Variable(
                        id='var_ACALD_reduced_cost',
                        target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']/@reducedCost",
                        target_namespaces=self.NAMESPACES,
                        task=doc.tasks[0],
                    ),
                ],
                math='var_ACALD_reduced_cost',
            ))
            doc.data_generators.append(sedml_data_model.DataGenerator(
                id='data_gen_THD2_reduced_cost',
                variables=[
                    sedml_data_model.Variable(
                        id='var_THD2_reduced_cost',
                        target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_THD2']/@reducedCost",
                        target_namespaces=self.NAMESPACES,
                        task=doc.tasks[0],
                    ),
                ],
                math='var_THD2_reduced_cost',
            ))
            doc.data_generators.append(sedml_data_model.DataGenerator(
                id='data_gen_13dpg_c_shadow_price',
                variables=[
                    sedml_data_model.Variable(
                        id='var_13dpg_c_shadow_price',
                        target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='13dpg_c']/@shadowPrice",
                        target_namespaces=self.NAMESPACES,
                        task=doc.tasks[0],
                    ),
                ],
                math='var_13dpg_c_shadow_price',
            ))
            doc.data_generators.append(sedml_data_model.DataGenerator(
                id='data_gen_succ_c_shadow_price',
                variables=[
                    sedml_data_model.Variable(
                        id='var_succ_c_shadow_price',
                        target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_succ_c']/@shadowPrice",
                        target_namespaces=self.NAMESPACES,
                        task=doc.tasks[0],
                    ),
                ],
                math='var_succ_c_shadow_price',
            ))
            doc.outputs.append(sedml_data_model.Report(
                id='report_1',
                data_sets=[
                    sedml_data_model.DataSet(id='data_set_ACONTa_flux', label='ACONTa_flux', data_generator=doc.data_generators[0]),
                    sedml_data_model.DataSet(id='data_set_TALA_flux', label='TALA_flux', data_generator=doc.data_generators[1]),
                    sedml_data_model.DataSet(id='data_set_ACALD_reduced_cost', label='ACALD_reduced_cost',
                                             data_generator=doc.data_generators[2]),
                    sedml_data_model.DataSet(id='data_set_THD2_reduced_cost', label='THD2_reduced_cost',
                                             data_generator=doc.data_generators[3]),
                    sedml_data_model.DataSet(id='data_set_13dpg_c_shadow_price', label='13dpg_c_shadow_price',
                                             data_generator=doc.data_generators[4]),
                    sedml_data_model.DataSet(id='data_set_succ_c_shadow_price', label='succ_c_shadow_price',
                                             data_generator=doc.data_generators[5]),
                ],
            ))
        else:
            doc.data_generators.append(sedml_data_model.DataGenerator(
                id='data_gen_ACONTa_min_flux',
                variables=[
                    sedml_data_model.Variable(
                        id='var_ACONTa_min_flux',
                        target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='ACONTa']/@minFlux",
                        target_namespaces=self.NAMESPACES,
                        task=doc.tasks[0],
                    ),
                ],
                math='var_ACONTa_min_flux',
            ))
            doc.data_generators.append(sedml_data_model.DataGenerator(
                id='data_gen_ACONTa_max_flux',
                variables=[
                    sedml_data_model.Variable(
                        id='var_ACONTa_max_flux',
                        target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='ACONTa']/@maxFlux",
                        target_namespaces=self.NAMESPACES,
                        task=doc.tasks[0],
                    ),
                ],
                math='var_ACONTa_max_flux',
            ))
            doc.data_generators.append(sedml_data_model.DataGenerator(
                id='data_gen_SUCDi_min_flux',
                variables=[
                    sedml_data_model.Variable(
                        id='var_SUCDi_min_flux',
                        target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_SUCDi']/@minFlux",
                        target_namespaces=self.NAMESPACES,
                        task=doc.tasks[0],
                    ),
                ],
                math='var_SUCDi_min_flux',
            ))
            doc.data_generators.append(sedml_data_model.DataGenerator(
                id='data_gen_SUCDi_max_flux',
                variables=[
                    sedml_data_model.Variable(
                        id='var_SUCDi_max_flux',
                        target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_SUCDi']/@maxFlux",
                        target_namespaces=self.NAMESPACES,
                        task=doc.tasks[0],
                    ),
                ],
                math='var_SUCDi_max_flux',
            ))
            doc.outputs.append(sedml_data_model.Report(
                id='report_1',
                data_sets=[
                    sedml_data_model.DataSet(id='data_set_ACONTa_min_flux', label='ACONTa_min_flux', data_generator=doc.data_generators[0]),
                    sedml_data_model.DataSet(id='data_set_ACONTa_max_flux', label='ACONTa_max_flux', data_generator=doc.data_generators[1]),
                    sedml_data_model.DataSet(id='data_set_SUCDi_min_flux', label='SUCDi_min_flux', data_generator=doc.data_generators[2]),
                    sedml_data_model.DataSet(id='data_set_SUCDi_max_flux', label='SUCDi_max_flux', data_generator=doc.data_generators[3]),
                ],
            ))

        append_all_nested_children_to_doc(doc)

        return doc

    def _assert_combine_archive_outputs(self, doc, out_dir):
        self.assertEqual(set(['reports.h5']).difference(set(os.listdir(out_dir))), set())

        report = doc.outputs[0]
        report_results = ReportReader().run(report, out_dir, 'sim_1.sedml/report_1', format=report_data_model.ReportFormat.h5)

        self.assertEqual(sorted(report_results.keys()), sorted([d.id for d in doc.outputs[0].data_sets]))

        sim = doc.tasks[0].simulation
        self.assertEqual(report_results[report.data_sets[0].id].size, 1)

        if sim.algorithm.kisao_id == 'KISAO_0000437':
            expected_results = {
                'data_set_ACONTa_flux': 6.007250,
                'data_set_TALA_flux': 1.496984,
                'data_set_ACALD_reduced_cost': 6.938894e-18,
                'data_set_THD2_reduced_cost': -2.546243e-03,
                'data_set_13dpg_c_shadow_price': -0.047105,
                'data_set_succ_c_shadow_price': -0.050925,
            }

        elif sim.algorithm.kisao_id == 'KISAO_0000528':
            expected_results = {
                'data_set_ACONTa_flux': 6.007250e+00,
                'data_set_TALA_flux': 1.496984e+00,
                'data_set_ACALD_reduced_cost': -2.000000,
                'data_set_THD2_reduced_cost': 3.822222,
                'data_set_13dpg_c_shadow_price': 18.911111,
                'data_set_succ_c_shadow_price': 9.844444,
            }

        elif sim.algorithm.kisao_id == 'KISAO_0000527':
            expected_results = {
                'data_set_ACONTa_flux': 6.007250e+00,
                'data_set_TALA_flux': 1.496984e+00,
                'data_set_ACALD_reduced_cost': numpy.nan,
                'data_set_THD2_reduced_cost': numpy.nan,
                'data_set_13dpg_c_shadow_price': numpy.nan,
                'data_set_succ_c_shadow_price': numpy.nan,
            }

        elif sim.algorithm.kisao_id == 'KISAO_0000526':
            expected_results = {
                'data_set_ACONTa_min_flux': 6.007250e+00,
                'data_set_ACONTa_max_flux': 6.007250e+00,
                'data_set_SUCDi_min_flux': 5.064376e+00,
                'data_set_SUCDi_max_flux': 1e3,
            }

        for data_set_id, expected_result in expected_results.items():
            numpy.testing.assert_allclose(report_results[data_set_id], numpy.array(expected_result), rtol=1e-4, atol=1e-8)

    def test_exec_sedml_docs_in_combine_archive_with_all_algorithms(self):
        for alg in gen_algorithms_from_specs(os.path.join(os.path.dirname(__file__), '..', 'biosimulators.json')).values():
            doc, archive_filename = self._build_combine_archive(algorithm=alg)
            out_dir = os.path.join(self.dirname, alg.kisao_id)
            core.exec_sedml_docs_in_combine_archive(archive_filename, out_dir,
                                                    report_formats=[
                                                        report_data_model.ReportFormat.h5,
                                                    ],
                                                    bundle_outputs=True,
                                                    keep_individual_outputs=True)

            self._assert_combine_archive_outputs(doc, out_dir)

    def test_raw_cli(self):
        with mock.patch('sys.argv', ['', '--help']):
            with self.assertRaises(SystemExit) as context:
                __main__.main()
                self.assertRegex(context.Exception, 'usage: ')

    def test_exec_sedml_docs_in_combine_archive_with_cli(self):
        doc, archive_filename = self._build_combine_archive()
        out_dir = os.path.join(self.dirname, 'out')
        env = self._get_combine_archive_exec_env()

        with mock.patch.dict(os.environ, env):
            with __main__.App(argv=['-i', archive_filename, '-o', out_dir]) as app:
                app.run()

        self._assert_combine_archive_outputs(doc, out_dir)

    def _get_combine_archive_exec_env(self):
        return {
            'REPORT_FORMATS': 'h5'
        }

    def test_exec_sedml_docs_in_combine_archive_with_docker_image(self):
        doc, archive_filename = self._build_combine_archive()
        out_dir = os.path.join(self.dirname, 'out')
        docker_image = self.DOCKER_IMAGE
        env = self._get_combine_archive_exec_env()

        exec_sedml_docs_in_archive_with_containerized_simulator(
            archive_filename, out_dir, docker_image, environment=env, pull_docker_image=False)

        self._assert_combine_archive_outputs(doc, out_dir)
