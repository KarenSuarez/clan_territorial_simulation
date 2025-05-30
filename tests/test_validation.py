# clan_territorial_simulation/tests/test_validation.py
import unittest
from analysis.validation import check_conservation_laws, load_conservation_tests, generate_conservation_report, check_conservation_alert
from simulation.engine import SimulationEngine
from models.environment import Environment
from models.clan import Clan
import numpy as np
import json

class TestConservationLaws(unittest.TestCase):
    def test_population_conservation(self):
        initial_state = {'clans': [{'id': 1, 'size': 10}, {'id': 2, 'size': 5}], 'resource_grid': np.zeros((10, 10)).tolist()}
        final_state = {'clans': [{'id': 1, 'size': 10}, {'id': 2, 'size': 5}], 'resource_grid': np.ones((10, 10)).tolist()}
        results = check_conservation_laws(initial_state, final_state)
        self.assertTrue(results['population_conserved'])

    def test_resource_conservation(self):
        initial_state = {'clans': [{'id': 1, 'size': 10}], 'resource_grid': np.ones((5, 5)).tolist()}
        final_state = {'clans': [{'id': 1, 'size': 8}], 'resource_grid': np.ones((5, 5)).tolist()}
        results = check_conservation_laws(initial_state, final_state)
        self.assertTrue(results['resource_conserved'])

    def test_conservation_failure(self):
        initial_state = {'clans': [{'id': 1, 'size': 10}], 'resource_grid': np.zeros((5, 5)).tolist()}
        final_state = {'clans': [{'id': 1, 'size': 12}], 'resource_grid': np.ones((5, 5)).tolist()}
        results = check_conservation_laws(initial_state, final_state)
        self.assertFalse(results['population_conserved'])
        self.assertFalse(results['resource_conserved'])

    def test_load_conservation_tests(self):
        # Create a dummy test file
        test_data = [{"initial": {'clans': [{'id': 1, 'size': 5}], 'resource_grid': [[10]]},
                      "final": {'clans': [{'id': 1, 'size': 5}], 'resource_grid': [[10]]}}]
        with open("data/validation/temp_conservation_tests.json", 'w') as f:
            json.dump(test_data, f)
        tests = load_conservation_tests("data/validation/temp_conservation_tests.json")
        self.assertEqual(len(tests), 1)
        self.assertEqual(tests[0]['initial']['clans'][0]['size'], 5)
        import os
        os.remove("data/validation/temp_conservation_tests.json")

    def test_conservation_report_generation(self):
        results_passed = {'population_conserved': True, 'initial_population': 15, 'final_population': 15,
                          'resource_conserved': True, 'initial_resource': 25, 'final_resource': 25}
        report_passed = generate_conservation_report(results_passed)
        self.assertIn("PASSED", report_passed)

        results_failed = {'population_conserved': False, 'initial_population': 10, 'final_population': 12,
                          'resource_conserved': False, 'initial_resource': 20, 'final_resource': 18}
        report_failed = generate_conservation_report(results_failed)
        self.assertIn("FAILED", report_failed)
        self.assertIn("Población Inicial: 10.00", report_failed)
        self.assertIn("Recursos Finales: 18.00", report_failed)

    def test_conservation_alert_generation(self):
        results_passed = {'population_conserved': True, 'resource_conserved': True}
        alerts_passed = check_conservation_alert(results_passed)
        self.assertEqual(len(alerts_passed), 0)

        results_failed_pop = {'population_conserved': False, 'initial_population': 10, 'final_population': 10.00001, 'resource_conserved': True}
        alerts_failed_pop = check_conservation_alert(results_failed_pop)
        self.assertEqual(len(alerts_failed_pop), 1)
        self.assertIn("ALERTA: Violación de conservación de población", alerts_failed_pop[0])

        results_failed_res = {'population_conserved': True, 'resource_conserved': False, 'initial_resource': 20, 'final_resource': 20.00001}
        alerts_failed_res = check_conservation_alert(results_failed_res)
        self.assertEqual(len(alerts_failed_res), 1)
        self.assertIn("ALERTA: Violación de conservación de recursos", alerts_failed_res[0])

if __name__ == '__main__':
    unittest.main()