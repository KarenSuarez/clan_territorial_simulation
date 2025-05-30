# clan_territorial_simulation/tests/test_models.py
import unittest
import numpy as np
from models.clan import Clan
from models.environment import Environment
from models.resource import ResourceGrid

class TestClanModel(unittest.TestCase):
    def test_clan_creation(self):
        clan = Clan(1, 10, [5, 5])
        self.assertEqual(clan.id, 1)
        self.assertEqual(clan.size, 10)
        np.testing.assert_array_equal(clan.position, [5, 5])

    def test_clan_movement(self):
        clan = Clan(1, 10, [5, 5])
        clan.move([10, 10])
        np.testing.assert_array_equal(clan.position, [10, 10])

    def test_clan_forrage(self):
        environment = ResourceGrid(initial_distribution='uniform')
        clan = Clan(1, 10, [5, 5], parameters={'resource_required_per_individual': 1.0})
        initial_resource = environment.get_resource([5, 5])
        consumption_rate = clan.forrage(environment, 1.0)
        final_resource = environment.get_resource([5, 5])
        self.assertLessEqual(consumption_rate, 10.0)
        self.assertLessEqual(final_resource, initial_resource)

    def test_clan_starvation_mortality(self):
        clan = Clan(1, 10, [5, 5])
        mortality_high = clan.calculate_starvation_mortality(0.5)
        mortality_low = clan.calculate_starvation_mortality(10.0)
        self.assertGreater(mortality_high, mortality_low)
        self.assertGreaterEqual(mortality_high, 0)
        self.assertGreaterEqual(mortality_low, 0)

class TestEnvironmentModel(unittest.TestCase):
    def test_environment_creation(self):
        environment = Environment(grid_size=(10, 10))
        self.assertEqual(environment.grid_size.tolist(), [10, 10])
        self.assertEqual(environment.grid.shape, (10, 10))

    def test_environment_valid_position(self):
        environment = Environment(grid_size=(10, 10))
        self.assertTrue(environment.is_valid_position([5, 5]))
        self.assertFalse(environment.is_valid_position([-1, 5]))
        self.assertFalse(environment.is_valid_position([5, 10]))

    def test_environment_toroidal_position(self):
        environment = Environment(grid_size=(10, 10))
        np.testing.assert_array_equal(environment.get_toroidal_position([12, 3]), [2, 3])
        np.testing.assert_array_equal(environment.get_toroidal_position([-1, 7]), [9, 7])

    def test_environment_resource_update(self):
        environment = ResourceGrid(grid_size=(10, 10), initial_distribution='uniform')
        initial_resource = environment.get_resource([3, 3])
        environment.consume([3, 3], 5)
        final_resource = environment.get_resource([3, 3])
        self.assertEqual(final_resource, initial_resource - 5)
        environment.regenerate(1.0)
        self.assertGreater(environment.get_resource([3, 3]), final_resource)

class TestResourceGridModel(unittest.TestCase):
    def test_resource_grid_creation(self):
        grid = ResourceGrid(grid_size=(5, 5))
        self.assertEqual(grid.grid_size.tolist(), [5, 5])
        self.assertEqual(grid.grid.shape, (5, 5))
        self.assertTrue(np.all(grid.grid == 100.0)) # Default RESOURCE_MAX

    def test_resource_grid_consumption(self):
        grid = ResourceGrid(grid_size=(5, 5))
        initial_resource = grid.get_resource([1, 1])
        consumed = grid.consume([1, 1], 20)
        final_resource = grid.get_resource([1, 1])
        self.assertEqual(consumed, 20)
        self.assertEqual(final_resource, initial_resource - 20)
        consumed_more = grid.consume([1, 1], 100)
        self.assertEqual(consumed_more, final_resource)
        self.assertEqual(grid.get_resource([1, 1]), 0)

    def test_resource_grid_regeneration(self):
        grid = ResourceGrid(grid_size=(5, 5))
        grid.consume([2, 2], 50)
        initial_resource = grid.get_resource([2, 2])
        grid.regenerate(1.0)
        final_resource = grid.get_resource([2, 2])
        self.assertGreater(final_resource, initial_resource)
        self.assertLessEqual(final_resource, 100.0)

if __name__ == '__main__':
    unittest.main()