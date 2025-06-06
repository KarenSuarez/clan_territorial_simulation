# clan_territorial_simulation/simulation/modes.py

import numpy as np
import random
import json
# No se importa config aquí directamente, los parámetros vienen en el diccionario config.
# from config import GRID_SIZE 
from .random_generators import MersenneTwister

class SimulationMode:
    def __init__(self, config_path=None, seed=None):
        self.config = self.load_mode_config(config_path) if config_path else {}
        self.seed = seed
        self.rng = MersenneTwister(seed) if seed is not None else MersenneTwister(random.randint(0, 10000000))

    def load_mode_config(self, config_path):
        """Carga la configuración específica del modo."""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {} # Retornar un diccionario vacío si no se encuentra el archivo

    def apply_clan_behavior(self, clan, environment, dt):
        raise NotImplementedError("Subclasses must implement this method")

class StochasticMode(SimulationMode):
    def __init__(self, config_path=None, seed=None):
        super().__init__(config_path, seed)
        # Asegurar que el RNG del clan sea el del modo
        # Esto se hará en el engine, al crear los clanes o antes de cada paso.
        # clan.set_rng(self.rng) # Esto no se hace aquí, sino en el engine

    def apply_clan_behavior(self, clan, environment, dt):
        """Comportamiento con elementos aleatorios para el clan."""
        clan.set_rng(self.rng) # Asegurar que el clan use el RNG del modo

        # Movimiento con ruido aleatorio y gradiente de recursos
        # El clan calcula su propia dirección óptima y el modo le añade ruido
        resource_direction = clan._find_resource_direction(environment) # Método del clan
        
        movement_noise_std = self.config.get('movement_noise_std', 0.1) # Valor por defecto

        # Generar ruido con el RNG del modo
        noise = self.rng.random_normal(0, movement_noise_std, size=2)
        
        # Combinar dirección de recurso y ruido
        # Si no hay dirección de recurso (ej. todo explorado), solo moverse aleatoriamente
        effective_direction = resource_direction
        if np.linalg.norm(resource_direction) > 0:
            effective_direction = resource_direction + noise
            effective_direction = effective_direction / (np.linalg.norm(effective_direction) + 1e-6) # Normalizar

        else: # Si no hay un recurso claro, el ruido puede ser la dirección dominante
            effective_direction = noise
            if np.linalg.norm(effective_direction) > 0:
                effective_direction = effective_direction / np.linalg.norm(effective_direction)


        clan._move(effective_direction * clan.parameters['movement_speed'] * dt, environment)

        # Forrajeo probabilístico
        forage_probability = self.config.get('forage_probability', 0.8)
        if self.rng.random_float() < forage_probability:
            # El forrajeo se maneja ahora dentro de _consume_resources en Clan
            # pero el modo puede decidir si el clan "intenta" forrajear
            clan._forage_behavior(environment, dt) # Simplemente llama al comportamiento de forrajeo del clan


class DeterministicMode(SimulationMode):
    def __init__(self, config_path=None, seed=None):
        super().__init__(config_path, seed)
        self.optimal_step_cache = {} # Cache para optimizaciones deterministas

    def apply_clan_behavior(self, clan, environment, dt):
        """Comportamiento optimizado y determinista para el clan."""
        clan.set_rng(self.rng) # Asegurar que el clan use el RNG del modo (aunque sea fijo)

        # 1. Optimización del Movimiento (Gradiente Descendente hacia mayor recurso)
        # El clan ya tiene el método _find_resource_direction que es determinista
        optimal_direction = clan._find_resource_direction(environment)
        
        # Aplicar el movimiento directo
        clan._move(optimal_direction * clan.parameters['movement_speed'] * dt, environment)

        # 2. Optimización del Forrajeo (Heurística basada en distancia y densidad)
        # El forrajeo se maneja ahora dentro de _consume_resources en Clan
        # Aquí, simplemente aseguramos que el clan siempre intente forrajear si es su estado
        if clan.state == 'foraging': # O si hay recursos disponibles
            clan._forage_behavior(environment, dt) # Llama al comportamiento de forrajeo del clan

        # 3. Resolución de Conflictos
        # La lógica de conflicto en el Engine._process_interactions ya es semi-determinista
        # y se basa en cercanía y estrategias. No se necesita lógica extra aquí.
        pass