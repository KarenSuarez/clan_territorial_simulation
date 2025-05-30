# clan_territorial_simulation/simulation/engine.py
import numpy as np
from models.equations import population_dynamics, clan_movement
from .random_generators import MersenneTwister

class SimulationEngine:
    def __init__(self, environment, initial_clans, simulation_mode=None):
        self.environment = environment
        self.clans = list(initial_clans)
        self.time = 0.0
        self.dt = 0.1 # Default time step
        self.simulation_mode = simulation_mode if simulation_mode else None

    def step(self):
        dt = self.dt

        # 1. Regenerate resources
        self.environment.regenerate(dt)

        # 2. Clan actions and population dynamics
        for clan in self.clans:
            if clan.size <= 0:
                continue

            # Apply behavior based on the simulation mode
            if self.simulation_mode:
                self.simulation_mode.apply_clan_behavior(clan, self.environment, dt)
                starvation_rate = clan.calculate_starvation_mortality(self.get_available_resource_per_capita(clan))
                competition_rate = self.calculate_competition_mortality(clan) # Placeholder

                dn_dt = population_dynamics(
                    clan.size,
                    clan.parameters['birth_rate'],
                    clan.parameters['natural_death_rate'],
                    competition_rate,
                    starvation_rate
                )
                clan.size += dn_dt * dt
                clan.size = max(0, int(clan.size))

        # Remove extinct clans
        self.clans = [clan for clan in self.clans if clan.size > 0]

        self.time += dt

    def get_available_resource_per_capita(self, clan):
        local_resource = self.environment.get_resource(clan.position.astype(int))
        return local_resource / clan.size if clan.size > 0 else 0

    def calculate_competition_mortality(self, clan):
        # Placeholder for competition mortality
        return 0.01

    def get_simulation_state(self):
        return {
            'time': self.time,
            'clans': [{'id': c.id, 'size': c.size, 'position': c.position.tolist()} for c in self.clans],
            'resource_grid': self.environment.grid.tolist()
        }