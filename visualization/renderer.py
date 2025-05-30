# clan_territorial_simulation/visualization/renderer.py
import numpy as np
from config import GRID_SIZE

class SimulationRenderer:
    def __init__(self):
        self.grid_x, self.grid_y = GRID_SIZE

    def render_state(self, simulation_state):
        """
        Genera un diccionario JSON serializable con el estado de la simulación para el frontend.
        """
        resource_data = simulation_state.get('resource_grid', np.zeros(GRID_SIZE).tolist())
        clan_data = []
        for clan in simulation_state.get('clans', []):
            clan_data.append({
                'id': clan['id'],
                'size': clan['size'],
                'position': [int(p) for p in clan['position']]
            })
        return {
            'time': simulation_state.get('time', 0),
            'resource_grid': resource_data,
            'clans': clan_data
        }