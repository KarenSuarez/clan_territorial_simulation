# clan_territorial_simulation/models/resource.py
import numpy as np
from config import GRID_SIZE, RESOURCE_MAX, RESOURCE_REGEN_RATE

class ResourceGrid:
    def __init__(self, initial_distribution='uniform'):
        self.grid_size = np.array(GRID_SIZE)
        self.grid = np.zeros(GRID_SIZE)
        if initial_distribution == 'uniform':
            self.grid[:] = RESOURCE_MAX  # Inicialmente recursos máximos en todas las celdas

    def regenerate(self, dt):
        self.grid = np.clip(self.grid + RESOURCE_REGEN_RATE * RESOURCE_MAX * (1 - self.grid / RESOURCE_MAX) * dt, 0, RESOURCE_MAX)

    def consume(self, position, amount):
        pos = np.mod(np.array(position).astype(int), self.grid_size)
        if self.grid[pos[0], pos[1]] >= amount:
            self.grid[pos[0], pos[1]] -= amount
            return amount
        else:
            consumed = self.grid[pos[0], pos[1]]
            self.grid[pos[0], pos[1]] = 0
            return consumed

    def get_resource(self, position):
        pos = np.mod(np.array(position).astype(int), self.grid_size)
        return self.grid[pos[0], pos[1]]

    def __repr__(self):
        return f"ResourceGrid(size={self.grid_size})"