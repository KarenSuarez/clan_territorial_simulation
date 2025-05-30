# clan_territorial_simulation/models/clan.py
import numpy as np
from .territory import Territory
from .equations import starvation_mortality, cooperative_consumption
from config import RESOURCE_REQUIRED_PER_INDIVIDUAL

class Clan:
    def __init__(self, clan_id, initial_size, initial_position, parameters=None):
        self.id = clan_id
        self.size = initial_size
        self.position = np.array(initial_position, dtype=float)
        self.territory = Territory()
        self.parameters = parameters or {
            'birth_rate': 0.1,
            'natural_death_rate': 0.05,
            'aggression': 0.5,
            'foraging_efficiency': 0.1,
            'cooperative_lambda': 0.8,
            'movement_speed': 1.0,
            'perception_radius': 5,
            'resource_required_per_individual': RESOURCE_REQUIRED_PER_INDIVIDUAL
        }

    def move(self, new_position):
        self.position = np.array(new_position, dtype=float)

    def update_territory(self, new_area):
        self.territory.area = new_area

    def forrage(self, environment, dt):
        if self.size > 0:
            resource_available = environment.get_resource(self.position.astype(int))
            resource_needed = self.size * self.parameters['resource_required_per_individual'] * dt
            consumed = environment.consume(self.position.astype(int), min(resource_available, resource_needed))
            return consumed / dt
        return 0.0

    def calculate_starvation_mortality(self, available_resource_per_capita):
        if self.size > 0:
            return starvation_mortality(available_resource_per_capita)
        return 0.0

    def calculate_cooperative_consumption_rate(self, local_resource_concentration):
        return cooperative_consumption(
            1,
            self.size,
            self.parameters['cooperative_lambda'],
            local_resource_concentration,
            self.parameters['foraging_efficiency']
        )

    def get_perceived_resource_gradient(self, environment):
        gradient = np.array([0.0, 0.0])
        x, y = self.position.astype(int)
        perception_radius = int(self.parameters['perception_radius'])

        for dx in range(-perception_radius, perception_radius + 1):
            for dy in range(-perception_radius, perception_radius + 1):
                nx = (x + dx) % environment.grid_size[0]
                ny = (y + dy) % environment.grid_size[1]
                if dx != 0 or dy != 0:
                    resource_diff_x = environment.get_resource((nx + 1) % environment.grid_size[0], ny) - environment.get_resource(nx, ny)
                    resource_diff_y = environment.get_resource(nx, (ny + 1) % environment.grid_size[1]) - environment.get_resource(nx, ny)
                    gradient += np.array([resource_diff_x, resource_diff_y])

        norm = np.linalg.norm(gradient)
        if norm > 0:
            return gradient / norm
        return np.array([0.0, 0.0])

    def __repr__(self):
        return f"Clan(id={self.id}, size={self.size}, pos={self.position.round(2)})"