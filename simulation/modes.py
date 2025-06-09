import numpy as np
import random
import json
import os
from .random_generators import MersenneTwister

class SimulationMode:
    def __init__(self, config_path=None, seed=None):
        self.config = self.load_mode_config(config_path) if config_path else {}
        self.seed = seed
        self.rng = MersenneTwister(seed) if seed is not None else MersenneTwister(random.randint(0, 10000000))

    def load_mode_config(self, config_path):
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}

    def apply_clan_behavior(self, clan, environment, dt):
        raise NotImplementedError("Subclasses must implement this method")

class StochasticMode(SimulationMode):
    def __init__(self, config_path=None, seed=None):
        super().__init__(config_path, seed)
        default_stochastic_config = {
            'movement_noise_std': 0.1,
            'forage_probability': 0.8,
            'decision_noise_factor': 0.15,
            'interaction_randomness': 0.2,
            'state_transition_noise': 0.1
        }
        for key, value in default_stochastic_config.items():
            if key not in self.config:
                self.config[key] = value

    def apply_clan_behavior(self, clan, environment, dt):
        clan.set_rng(self.rng)
        clan.update_behavior(environment, [], dt)
        self._apply_stochastic_behavior(clan, environment, dt)

    def _apply_stochastic_behavior(self, clan, environment, dt):
        if clan.state == 'foraging':
            self._stochastic_foraging(clan, environment, dt)
        elif clan.state == 'migrating':
            self._stochastic_migration(clan, environment, dt)
        elif clan.state == 'resting':
            self._stochastic_resting(clan, dt)
        elif clan.state == 'defending':
            self._stochastic_defending(clan, environment, dt)
        elif clan.state == 'fighting':
            self._stochastic_fighting_movement(clan, environment, dt)

    def _stochastic_foraging(self, clan, environment, dt):
        forage_probability = self.config.get('forage_probability', 0.8)
        if self.rng.random_float() < forage_probability:
            resource_direction = clan._find_resource_direction(environment)
            movement_noise_std = self.config.get('movement_noise_std', 0.1)
            noise = self.rng.random_normal(0, movement_noise_std, size=2)
            if np.linalg.norm(resource_direction) > 0:
                effective_direction = resource_direction + noise
                if np.linalg.norm(effective_direction) > 0:
                    effective_direction = effective_direction / np.linalg.norm(effective_direction)
            else:
                effective_direction = noise
                if np.linalg.norm(effective_direction) > 0:
                    effective_direction = effective_direction / np.linalg.norm(effective_direction)
            movement = effective_direction * clan.parameters['movement_speed'] * dt
        else:
            random_angle = self.rng.random_uniform(0, 2 * np.pi)
            random_direction = np.array([np.cos(random_angle), np.sin(random_angle)])
            movement = random_direction * clan.parameters['movement_speed'] * 0.5 * dt
        clan._move(movement, environment)

    def _stochastic_migration(self, clan, environment, dt):
        migration_direction = clan._find_migration_direction(environment)
        noise_factor = self.config.get('decision_noise_factor', 0.15)
        noise = self.rng.random_normal(0, noise_factor, size=2)
        if np.linalg.norm(migration_direction) > 0:
            noisy_direction = migration_direction + noise
            if np.linalg.norm(noisy_direction) > 0:
                noisy_direction = noisy_direction / np.linalg.norm(noisy_direction)
        else:
            random_angle = self.rng.random_uniform(0, 2 * np.pi)
            noisy_direction = np.array([np.cos(random_angle), np.sin(random_angle)])
        movement = noisy_direction * clan.parameters['movement_speed'] * 1.5 * dt
        clan._move(movement, environment)
        energy_cost_variation = self.rng.random_normal(0, 3) * dt
        clan.energy = max(0, clan.energy - (10 + energy_cost_variation) * dt)

    def _stochastic_resting(self, clan, dt):
        base_recovery = 25
        recovery_variation = self.rng.random_normal(0, 5)
        energy_gain = (base_recovery + recovery_variation) * dt
        clan.energy = min(100, clan.energy + energy_gain)
        moral_recovery = self.rng.random_normal(10, 2) * dt
        clan.morale = min(100, clan.morale + moral_recovery)
        noise = self.rng.random_normal(0, 0.05, size=2) * dt
        clan._move(noise, None)

    def _stochastic_defending(self, clan, environment, dt):
        if len(clan.territory_cells) > 0:
            territory_cells = list(clan.territory_cells)
            if territory_cells:
                target_cell_idx = self.rng.random_randint(0, len(territory_cells) - 1)
                target_cell = np.array(territory_cells[target_cell_idx])
                direction = target_cell - clan.position
                if np.linalg.norm(direction) > 1:
                    direction = direction / np.linalg.norm(direction)
                    noise = self.rng.random_normal(0, 0.1, size=2)
                    noisy_direction = direction + noise
                    if np.linalg.norm(noisy_direction) > 0:
                        noisy_direction = noisy_direction / np.linalg.norm(noisy_direction)
                    movement = noisy_direction * clan.parameters['movement_speed'] * 0.5 * dt
                    clan._move(movement, environment)
        moral_gain = self.rng.random_normal(1, 0.3) * dt
        clan.morale = min(100, clan.morale + moral_gain)

    def _stochastic_fighting_movement(self, clan, environment, dt):
        random_angle = self.rng.random_uniform(0, 2 * np.pi)
        random_direction = np.array([np.cos(random_angle), np.sin(random_angle)])
        movement = random_direction * clan.parameters['movement_speed'] * 0.3 * dt
        clan._move(movement, environment)

class DeterministicMode(SimulationMode):
    def __init__(self, config_path=None, seed=None):
        super().__init__(config_path, seed)
        self.optimal_step_cache = {}
        default_deterministic_config = {
            'movement_noise_std': 0.0,
            'forage_probability': 1.0,
            'optimization_level': 'basic',
            'use_caching': True
        }
        for key, value in default_deterministic_config.items():
            if key not in self.config:
                self.config[key] = value

    def apply_clan_behavior(self, clan, environment, dt):
        clan.set_rng(self.rng)
        clan.update_behavior(environment, [], dt)
        self._apply_deterministic_behavior(clan, environment, dt)

    def _apply_deterministic_behavior(self, clan, environment, dt):
        if clan.state == 'foraging':
            self._optimal_foraging(clan, environment, dt)
        elif clan.state == 'migrating':
            self._optimal_migration(clan, environment, dt)
        elif clan.state == 'resting':
            self._optimal_resting(clan, dt)
        elif clan.state == 'defending':
            self._optimal_defending(clan, environment, dt)
        elif clan.state == 'fighting':
            self._optimal_fighting_movement(clan, environment, dt)

    def _optimal_foraging(self, clan, environment, dt):
        optimal_direction = clan._find_resource_direction(environment)
        if np.linalg.norm(optimal_direction) > 0:
            movement = optimal_direction * clan.parameters['movement_speed'] * dt
            clan._move(movement, environment)

    def _optimal_migration(self, clan, environment, dt):
        cache_key = f"migration_{clan.id}_{int(clan.position[0])}_{int(clan.position[1])}"
        if self.config.get('use_caching', True) and cache_key in self.optimal_step_cache:
            optimal_direction = self.optimal_step_cache[cache_key]
        else:
            optimal_direction = clan._find_migration_direction(environment)
            if self.config.get('use_caching', True):
                self.optimal_step_cache[cache_key] = optimal_direction
        if np.linalg.norm(optimal_direction) > 0:
            movement = optimal_direction * clan.parameters['movement_speed'] * 1.5 * dt
            clan._move(movement, environment)
        clan.energy = max(0, clan.energy - 10 * dt)

    def _optimal_resting(self, clan, dt):
        clan.energy = min(100, clan.energy + 25 * dt)
        clan.morale = min(100, clan.morale + 10 * dt)

    def _optimal_defending(self, clan, environment, dt):
        if len(clan.territory_cells) > 0:
            territory_center = np.mean([np.array(cell) for cell in clan.territory_cells], axis=0)
            direction = territory_center - clan.position
            if np.linalg.norm(direction) > 1:
                direction = direction / np.linalg.norm(direction)
                movement = direction * clan.parameters['movement_speed'] * 0.5 * dt
                clan._move(movement, environment)
        clan.morale = min(100, clan.morale + 1 * dt)

    def _optimal_fighting_movement(self, clan, environment, dt):
        pass

    def get_optimization_stats(self):
        return {
            'cache_size': len(self.optimal_step_cache),
            'cache_enabled': self.config.get('use_caching', True),
            'optimization_level': self.config.get('optimization_level', 'basic')
        }

    def clear_cache(self):
        self.optimal_step_cache.clear()

    def update_cache_limit(self, max_entries=1000):
        if len(self.optimal_step_cache) > max_entries:
            items_to_remove = len(self.optimal_step_cache) - max_entries
            keys_to_remove = list(self.optimal_step_cache.keys())[:items_to_remove]
            for key in keys_to_remove:
                del self.optimal_step_cache[key]

class HybridMode(SimulationMode):
    def __init__(self, config_path=None, seed=None):
        super().__init__(config_path, seed)
        self.stochastic_mode = StochasticMode(config_path, seed)
        self.deterministic_mode = DeterministicMode(config_path, seed)
        default_hybrid_config = {
            'stochastic_ratio': 0.3,
            'decision_threshold': 0.5,
            'adaptive_switching': True
        }
        for key, value in default_hybrid_config.items():
            if key not in self.config:
                self.config[key] = value

    def apply_clan_behavior(self, clan, environment, dt):
        clan.set_rng(self.rng)
        clan.update_behavior(environment, [], dt)
        if self._should_use_stochastic_mode(clan, environment):
            self.stochastic_mode.apply_clan_behavior(clan, environment, dt)
        else:
            self.deterministic_mode.apply_clan_behavior(clan, environment, dt)

    def _should_use_stochastic_mode(self, clan, environment):
        if not self.config.get('adaptive_switching', True):
            return self.rng.random_float() < self.config.get('stochastic_ratio', 0.3)
        energy_factor = 1.0 - (clan.energy / 100.0)
        resource_factor = 1.0 - min(1.0, environment.get_local_resource_density(clan.position, 3) / 50.0)
        territory_factor = 1.0 - min(1.0, len(clan.territory_cells) / 20.0)
        stochastic_score = (energy_factor + resource_factor + territory_factor) / 3.0
        return stochastic_score > self.config.get('decision_threshold', 0.5)