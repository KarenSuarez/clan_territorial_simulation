# clan_territorial_simulation/tests/test_equations.py
import unittest
from models.equations import population_dynamics, resource_evolution, starvation_mortality, cooperative_consumption, clan_movement
import numpy as np

class TestEquationFunctions(unittest.TestCase):
    def test_population_dynamics(self):
        dn_dt = population_dynamics(10, 0.1, 0.05, 0.01, 0.02)
        self.assertEqual(dn_dt, (0.1 - 0.05 - 0.01 - 0.02) * 10)

    def test_resource_evolution(self):
        dr_dt = resource_evolution(50, 0.1, 2)
        self.assertEqual(dr_dt, 0.1 * 100 * (1 - 50 / 100) - 2)

    def test_starvation_mortality(self):
        mu_s_high = starvation_mortality(1)
        mu_s_low = starvation_mortality(10)
        self.assertGreater(mu_s_high, mu_s_low)
        self.assertGreaterEqual(mu_s_high, 0)
        self.assertGreaterEqual(mu_s_low, 0)

    def test_cooperative_consumption(self):
        consumption = cooperative_consumption(1, 5, 0.8, 0.5, 0.1)
        self.assertEqual(consumption, 1 * (5**(1-0.8)) * 0.5 * 0.1)

    def test_clan_movement(self):
        velocity = np.array([1.0, 0.5])
        gradient = np.array([0.8, 0.2])
        sigma = 0.1
        epsilon = np.array([0.3, -0.1])
        dpos_dt = clan_movement(velocity, gradient, sigma, epsilon)
        expected_dpos_dt = velocity * gradient + sigma * epsilon
        np.testing.assert_array_equal(dpos_dt, expected_dpos_dt)

if __name__ == '__main__':
    unittest.main()