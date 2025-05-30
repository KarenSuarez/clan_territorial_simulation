# clan_territorial_simulation/simulation/modes.py
import numpy as np
import random
import json
from config import GRID_SIZE
from .random_generators import MersenneTwister

class SimulationMode:
    def __init__(self, config_path=None, seed=None):
        self.config = self.load_config(config_path) if config_path else {}
        self.seed = seed
        self.rng = MersenneTwister(seed) if seed is not None else MersenneTwister(random.randint(0, 10000))

    def load_config(self, config_path):
        with open(config_path, 'r') as f:
            return json.load(f)

    def get_random_float(self):
        return self.rng.random_float()

    def get_random_normal(self, mean=0.0, std_dev=1.0):
        return self.rng.random_normal(mean, std_dev)

    def apply_clan_behavior(self, clan, environment, dt):
        raise NotImplementedError("Subclasses must implement this method")

class StochasticMode(SimulationMode):
    def __init__(self, config_path=None, seed=None):
        super().__init__(config_path, seed)

    def apply_clan_behavior(self, clan, environment, dt):
        # Comportamiento con elementos aleatorios
        # Movimiento con ruido aleatorio
        noise = self.config.get('movement_noise_std', 0.05) * np.array([self.get_random_normal(), self.get_random_normal()])
        gradient = clan.get_perceived_resource_gradient(environment)
        dpos_dt = clan.parameters['movement_speed'] * gradient + noise
        clan.move(clan.position + dpos_dt * dt)
        clan.position = environment.get_toroidal_position(clan.position)

        # Forrajeo probabilístico (ejemplo)
        if self.get_random_float() < self.config.get('forage_probability', 0.8):
            clan.forrage(environment, dt)

class DeterministicMode(SimulationMode):
    def __init__(self, config_path=None, seed=None):
        super().__init__(config_path, seed)
        self.optimal_step_cache = {} # Cache para optimizaciones

    def apply_clan_behavior(self, clan, environment, dt):
        # Comportamiento optimizado y determinista

        # 1. Optimización del Movimiento (Gradiente Descendente hacia mayor recurso)
        gradient = self.calculate_optimal_movement(clan, environment)
        clan.move(clan.position + clan.parameters['movement_speed'] * gradient * dt)
        clan.position = environment.get_toroidal_position(clan.position)

        # 2. Optimización del Forrajeo (Heurística basada en distancia y densidad)
        self.optimize_foraging(clan, environment, dt)

        # 3. Resolución de Conflictos (Simulación del equilibrio de Nash - simplificado)
        # En un modo completamente determinista, esto podría ser una regla fija basada en territorio
        # Por simplicidad, omitimos la implementación completa de Nash aquí y asumimos
        # el conflicto se resuelve basado en una regla predefinida o territorial.
        pass

    def calculate_optimal_movement(self, clan, environment):
        """Calcula el gradiente hacia la mayor concentración de recursos percibida."""
        key = (clan.id, tuple(clan.position.astype(int)))
        if key in self.optimal_step_cache:
            return self.optimal_step_cache[key]

        gradient = np.array([0.0, 0.0])
        x, y = clan.position.astype(int)
        perception_radius = int(clan.parameters['perception_radius'])
        max_resource = -1
        optimal_move = np.array([0.0, 0.0])

        for dx in range(-perception_radius, perception_radius + 1):
            for dy in range(-perception_radius, perception_radius + 1):
                nx = (x + dx) % environment.grid_size[0]
                ny = (y + dy) % environment.grid_size[1]
                if dx != 0 or dy != 0:
                    resource_level = environment.get_resource((nx, ny))
                    if resource_level > max_resource:
                        max_resource = resource_level
                        optimal_move = np.array([dx, dy], dtype=float)

        norm = np.linalg.norm(optimal_move)
        if norm > 0:
            optimal_move /= norm

        self.optimal_step_cache[key] = optimal_move
        return optimal_move

    def optimize_foraging(self, clan, environment, dt):
        """Heurística de forrajeo basada en la densidad local de recursos."""
        local_resource = environment.get_resource(clan.position.astype(int))
        resource_needed = clan.size * clan.parameters['resource_required_per_individual'] * dt
        if local_resource > 0:
            consumed = environment.consume(clan.position.astype(int), min(local_resource, resource_needed))
            return consumed / dt
        return 0.0

class SimulationScheduler:
    def __init__(self):
        self.time = 0.0
        self.events = []

    def add_event(self, time, callback, *args, **kwargs):
        self.events.append((time, callback, args, kwargs))
        self.events.sort(key=lambda item: item[0])

    def run_until(self, end_time):
        while self.events and self.events[0][0] <= end_time:
            time, callback, args, kwargs = self.events.pop(0)
            self.time = time
            callback(*args, **kwargs)

    def get_current_time(self):
        return self.time