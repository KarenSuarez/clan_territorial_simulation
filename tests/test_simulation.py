# clan_territorial_simulation/tests/test_simulation.py
import unittest
from simulation.engine import SimulationEngine
from models.environment import Environment
from models.clan import Clan
import numpy as np

class TestSimulationEngine(unittest.TestCase):
    def test_engine_creation(self):
        environment = Environment(grid_size=(10, 10))
        clans = [Clan(1, 5, [2, 2])]
        engine = SimulationEngine(environment, clans)
        self.assertIsNotNone(engine)
        self.assertEqual(len(engine.clans), 1)
        self.assertEqual(engine.time, 0.0)

    def test_engine_step(self):
        environment = Environment(grid_size=(10, 10))
        initial_clans = [Clan(1, 10, [3, 3], parameters={'birth_rate': 1.0, 'natural_death_rate': 0.0}),
                         Clan(2, 10, [7, 7], parameters={'birth_rate': 0.0, 'natural_death_rate': 1.0})]
        engine = SimulationEngine(environment, initial_clans, simulation_params={'dt': 0.1})
        initial_population = sum(clan.size for clan in engine.clans)
        initial_resource = np.sum(engine.environment.grid)
        engine.step()
        final_population = sum(clan.size for clan in engine.clans)
        final_resource = np.sum(engine.environment.grid)
        self.assertGreater(engine.time, 0.0)
        self.assertGreater(engine.clans[0].size, initial_clans[0].size) # Birth rate > death rate
        self.assertLess(engine.clans[1].size, initial_clans[1].size) # Death rate > birth rate
        self.assertLessEqual(final_resource, initial_resource) # Resources should be consumed

    def test_clan_extinction(self):
        environment = Environment(grid_size=(10, 10))
        clans = [Clan(1, 1, [5, 5], parameters={'natural_death_rate': 1.0})]
        engine = SimulationEngine(environment, clans, simulation_params={'dt': 1.0})
        self.assertEqual(len(engine.clans), 1)
        engine.step()
        self.assertEqual(len(engine.clans), 0)

if __name__ == '__main__':
    unittest.main()