import numpy as np
from config import GRID_SIZE

class Environment:
    def __init__(self, grid_size=GRID_SIZE):
        self.grid_size = np.array(grid_size)
        self.grid = np.zeros(grid_size)  # Inicialmente una rejilla vacía

    def is_valid_position(self, position):
        return 0 <= position[0] < self.grid_size[0] and 0 <= position[1] < self.grid_size[1]

    def get_toroidal_position(self, position):
        return np.mod(position, self.grid_size)

    def update_cell(self, position, value):
        pos = self.get_toroidal_position(np.array(position)).astype(int)
        self.grid[pos[0], pos[1]] = value

    def get_cell_value(self, position):
        pos = self.get_toroidal_position(np.array(position)).astype(int)
        return self.grid[pos[0], pos[1]]

    def __repr__(self):
        return f"Environment(size={self.grid_size})"