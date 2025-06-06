# models/clan.py - Versión refactorizada para trabajar con SimulationMode y Environment

import numpy as np

class Clan:
    def __init__(self, clan_id, initial_size, initial_position, parameters=None):
        self.id = clan_id
        self.size = max(1, int(initial_size))
        self.position = np.array(initial_position, dtype=float)

        # Estados básicos
        self.energy = 100.0
        self.morale = 100.0
        self.state = 'foraging' # foraging, defending, migrating, fighting, resting
        self.strategy = 'cooperative' # cooperative, aggressive, defensive, exploratory

        # Territorio y relaciones
        self.territory_cells = set()
        self.allies = set()
        self.enemies = set()

        # Memoria básica
        self.resource_memory = {}
        self.movement_history = [self.position.copy()]

        # Parámetros (valores por defecto si no se proporcionan)
        self.parameters = {
            'birth_rate': 0.1,
            'natural_death_rate': 0.05,
            'movement_speed': 1.0,
            'resource_required_per_individual': 0.1, # Coincidir con default_config
            'perception_radius': 5,
            'cooperation_tendency': 0.6,
            'aggressiveness': 0.3,
            'territorial_expansion_rate': 0.05, # Reducido para no crecer demasiado rápido
            'exploration_tendency': 0.5
        }

        if parameters:
            self.parameters.update(parameters)
        
        self.rng = None # El RNG será inyectado por el SimulationMode o Engine

        # print(f"Clan {self.id} creado: tamaño={self.size}, posición={self.position}")

    def set_rng(self, rng_instance):
        """Permite que el RNG se inyecte en el clan."""
        self.rng = rng_instance

    def update_behavior(self, environment, other_clans, dt):
        """
        Este método es el punto de entrada para que el SimulationMode aplique el comportamiento.
        El modo de simulación será el responsable de llamar a los métodos específicos de Clan
        (como _move, _forage_behavior, etc.) de manera estocástica o determinista.
        """
        # La lógica específica de movimiento, forrajeo, etc., ahora se activa desde el SimulationMode
        # Este método ahora solo se encarga de la percepción y decisión de estado,
        # y deja la ejecución del comportamiento al modo.

        try:
            self._perceive_environment(environment, other_clans)
            self._decide_state(environment, other_clans)
            # El modo es el que llama a los métodos de comportamiento después de esta decisión
            # No hay necesidad de llamar a _forage_behavior, _defend_behavior, etc. aquí directamente
            # _consume_resources y _update_territory se llaman directamente desde el engine después del apply_clan_behavior
            
        except Exception as e:
            print(f"Error en comportamiento del clan {self.id}: {e}")

    def _perceive_environment(self, environment, other_clans):
        """Percibe el entorno y otros clanes."""
        # Actualizar memoria de recursos cercanos
        radius = int(self.parameters['perception_radius'])
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                # Usar la función de distancia para percibir en un círculo, no un cuadrado
                if np.sqrt(dx*dx + dy*dy) <= radius: 
                    pos = self.position + np.array([dx, dy])
                    pos = environment.get_toroidal_position(pos).astype(int)
                    resource_level = environment.get_resource(pos)
                    self.resource_memory[tuple(pos)] = resource_level

    def _decide_state(self, environment, other_clans):
        """Decide qué estado adoptar."""
        threats = self._count_nearby_threats(other_clans)
        local_resources = self._evaluate_local_resources(environment)

        if threats > 0 and self.energy > 30:
            self.state = 'fighting' if self.size > 8 else 'defending'
        elif local_resources < self.size * self.parameters['resource_required_per_individual'] * 10 and self.energy > 20:
            self.state = 'migrating'
        elif self.energy < 25:
            self.state = 'resting'
        else:
            self.state = 'foraging'

    def _count_nearby_threats(self, other_clans):
        """Cuenta amenazas cercanas."""
        threats = 0
        for other_clan in other_clans:
            if other_clan.id != self.id:
                distance = np.linalg.norm(self.position - other_clan.position)
                # Considerar amenaza si está cerca y es más grande o igual
                if distance < self.parameters['perception_radius'] / 2 and other_clan.size >= self.size * 0.8:
                    threats += 1
        return threats

    def _evaluate_local_resources(self, environment):
        """Evalúa recursos en área local (promedio de recursos percibidos)."""
        if not self.resource_memory:
            return 0
        return sum(self.resource_memory.values()) / len(self.resource_memory)


    def _forage_behavior(self, environment, dt):
        """Comportamiento de forrajeo."""
        best_direction = self._find_resource_direction(environment)
        if np.linalg.norm(best_direction) > 0:
            movement = best_direction * self.parameters['movement_speed'] * dt
            self._move(movement, environment)
        # Consumir recursos se maneja en _consume_resources

    def _defend_behavior(self, environment, dt):
        """Comportamiento defensivo."""
        if len(self.territory_cells) > 0:
            territory_center = np.mean([np.array(cell) for cell in self.territory_cells], axis=0)
            direction = territory_center - self.position
            if np.linalg.norm(direction) > 1: # Si está lejos del centro, moverse hacia él
                direction = direction / np.linalg.norm(direction)
                movement = direction * self.parameters['movement_speed'] * 0.5 * dt
                self._move(movement, environment)
        # Aumentar moral ligeramente al defender
        self.morale = min(100, self.morale + 1 * dt)


    def _migrate_behavior(self, environment, dt):
        """Comportamiento de migración."""
        migration_direction = self._find_migration_direction(environment)
        if np.linalg.norm(migration_direction) > 0:
            movement = migration_direction * self.parameters['movement_speed'] * 1.5 * dt
            self._move(movement, environment)
        self.energy = max(0, self.energy - 10 * dt) # Mayor costo energético por migración

    def _fight_behavior(self, other_clans, dt):
        """Comportamiento de combate."""
        target = None
        min_distance = float('inf')

        # Buscar el enemigo más cercano y si está dentro del radio de combate
        for other_clan in other_clans:
            if other_clan.id != self.id and other_clan.size > 0:
                distance = np.linalg.norm(self.position - other_clan.position)
                if distance < min_distance and distance < 5: # Radio de combate
                    target = other_clan
                    min_distance = distance

        if target:
            # Moverse hacia el objetivo
            direction = target.position - self.position
            if np.linalg.norm(direction) > 0:
                direction = direction / np.linalg.norm(direction)
                movement = direction * self.parameters['movement_speed'] * 1.2 * dt
                self._move(movement, None) # No usar entorno para combate directo en movimiento

            # Combatir si está muy cerca
            if min_distance < 2: # Distancia para iniciar combate
                self._engage_combat(target, dt)
        else:
            # Si no hay enemigo cercano, vuelve a forrajear o defender
            self.state = 'foraging' # O 'defending' si aún está en territorio disputado


    def _rest_behavior(self, dt):
        """Comportamiento de descanso."""
        self.energy = min(100, self.energy + 25 * dt)
        self.morale = min(100, self.morale + 10 * dt)
        # Pequeño movimiento aleatorio para no estar completamente quieto
        if self.rng:
            noise = self.rng.random_normal(0, 0.05, size=2) * dt
            self._move(noise, None) # Moverse ligeramente sin referencia a recursos


    def _find_resource_direction(self, environment):
        """Encuentra la mejor dirección hacia recursos percibidos."""
        best_direction = np.array([0.0, 0.0])
        max_resource_level = -1.0
        
        # Iterar a través de la memoria de recursos
        for pos_tuple, resource_level in self.resource_memory.items():
            if resource_level > max_resource_level:
                cell_pos = np.array(pos_tuple)
                # Dirección hacia la celda con más recursos
                direction_vector = cell_pos - self.position
                # Ajustar para toroidalidad
                if environment:
                    direction_vector = environment.get_toroidal_position(direction_vector + environment.grid_size / 2) - environment.grid_size / 2

                if np.linalg.norm(direction_vector) > 0:
                    max_resource_level = resource_level
                    best_direction = direction_vector / np.linalg.norm(direction_vector)
        
        return best_direction


    def _find_migration_direction(self, environment):
        """Encuentra dirección para migración, buscando áreas con altos recursos no explorados."""
        best_direction = np.array([0.0, 0.0])
        best_score = -1.0

        # Para migración, buscar áreas con recursos altos y posiblemente poco exploradas
        # Usaremos una serie de puntos de prueba aleatorios
        for _ in range(self.parameters['perception_radius'] * 2): # Más intentos para mejor búsqueda
            if self.rng:
                angle = self.rng.random_uniform(0, 2*np.pi)
            else:
                angle = np.random.uniform(0, 2*np.pi) # Fallback

            direction_candidate = np.array([np.cos(angle), np.sin(angle)])
            test_pos = self.position + direction_candidate * self.parameters['perception_radius'] * 1.5 # Más lejos
            test_pos = environment.get_toroidal_position(test_pos).astype(int)

            # Evaluar recursos en el área objetivo del test_pos
            area_resources = 0
            cells_in_area = 0
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    check_pos = test_pos + np.array([dx, dy])
                    check_pos = environment.get_toroidal_position(check_pos).astype(int)
                    area_resources += environment.get_resource(check_pos)
                    cells_in_area += 1
            
            avg_area_resource = area_resources / cells_in_area if cells_in_area > 0 else 0

            # Dar bonus por áreas no visitadas recientemente (heurística de exploración)
            exploration_bonus = 0
            if tuple(test_pos) not in self.resource_memory or self.resource_memory[tuple(test_pos)] < 10: # Si la memoria es vieja o baja
                exploration_bonus = self.parameters['exploration_tendency'] * 20 # Mayor bonus para explorar

            current_score = avg_area_resource + exploration_bonus

            if current_score > best_score:
                best_score = current_score
                best_direction = direction_candidate

        return best_direction


    def _engage_combat(self, enemy, dt):
        """Combate entre clanes."""
        my_strength = self.size * (self.energy / 100) * self.parameters['aggressiveness']
        enemy_strength = enemy.size * (getattr(enemy, 'energy', 50) / 100) * enemy.parameters.get('aggressiveness', 0.3)

        total_strength = my_strength + enemy_strength
        if total_strength <= 0:
            return

        # Calcular daño
        damage_to_enemy = (my_strength / total_strength) * 3 * dt
        damage_to_me = (enemy_strength / total_strength) * 3 * dt

        # Aplicar daño
        enemy.size = max(0, enemy.size - damage_to_enemy)
        self.size = max(0, self.size - damage_to_me)

        # Efectos en energía
        self.energy = max(0, self.energy - 10 * dt)
        if hasattr(enemy, 'energy'):
            enemy.energy = max(0, enemy.energy - 10 * dt)

        # La moral se ve afectada por el combate
        self.morale = max(0, self.morale - 5 * dt)
        enemy.morale = max(0, enemy.morale - 5 * dt)


    def _consume_resources(self, environment, dt):
        """Consume recursos del entorno y actualiza energía y tamaño."""
        pos = self.position.astype(int)
        needed = self.size * self.parameters['resource_required_per_individual'] * dt

        # Eficiencia de grupo (cooperación)
        group_efficiency_bonus = self.parameters['cooperation_tendency'] * 0.3
        effective_consumption_rate = self.parameters['resource_required_per_individual'] * (1.0 - group_efficiency_bonus)
        effective_needed = self.size * effective_consumption_rate * dt

        consumed = environment.consume(pos, effective_needed)

        # Convertir recursos en energía
        if needed > 0:
            # Cuanta energía debería ganar vs. cuanto realmente consumió
            energy_conversion_efficiency = (consumed / effective_needed) if effective_needed > 0 else 0
            energy_gain = energy_conversion_efficiency * 15 * dt # 15 es un factor de conversión

            self.energy = min(100, self.energy + energy_gain)

        # Dinámica poblacional simple basada en energía y recursos
        # Esto se puede refinar usando equations.py en Solicitud 4
        current_birth_rate = self.parameters['birth_rate']
        current_death_rate = self.parameters['natural_death_rate']

        energy_factor_pop = (self.energy / 100.0) # 0 a 1
        
        # Efecto de la energía en la natalidad y mortalidad
        birth_modifier = max(0, (energy_factor_pop - 0.5) * 2) # Nace más si energía > 50
        death_modifier = max(0, (0.5 - energy_factor_pop) * 2) # Muere más si energía < 50

        # Cambio de tamaño
        size_change = (current_birth_rate * birth_modifier - current_death_rate * death_modifier) * self.size * dt
        self.size += size_change
        self.size = max(0, int(round(self.size)))


    def _move(self, movement_vector, environment):
        """Mueve el clan."""
        if environment:
            new_position = environment.get_toroidal_position(self.position + movement_vector)
        else:
            new_position = self.position + movement_vector

        self.position = new_position
        self.movement_history.append(self.position.copy())

        if len(self.movement_history) > 20: # Limitar historial para visualización
            self.movement_history.pop(0) # Eliminar el punto más antiguo

    def _update_territory(self):
        """Actualiza territorio controlado."""
        # Un clan reclama una celda si está cerca y tiene alta energía/moral
        expansion_chance = self.parameters['territorial_expansion_rate'] * (self.energy / 100) * (self.morale / 100)
        
        if self.rng:
            if self.rng.random_float() < expansion_chance:
                # Reclamar una celda adyacente aleatoria si hay RNG
                dx = self.rng.random_randint(-1, 1)
                dy = self.rng.random_randint(-1, 1)
                if dx != 0 or dy != 0:
                    cell = self.position.astype(int) + np.array([dx, dy])
                    self.territory_cells.add(tuple(cell))
        else: # Fallback sin RNG
            if np.random.random() < expansion_chance:
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        if dx == 0 and dy == 0:
                            continue
                        cell = self.position.astype(int) + np.array([dx, dy])
                        self.territory_cells.add(tuple(cell))


        # Limitar tamaño del territorio a algo razonable basado en el tamaño del clan
        max_territory_size = self.size * 5 # Cada individuo puede controlar 5 celdas
        if len(self.territory_cells) > max_territory_size:
            # Eliminar celdas más antiguas si la población es baja
            # O las más lejanas si no están contribuyendo
            
            # Simplificado: si el territorio es demasiado grande, lo reducimos
            # Esto puede ser más complejo con una verdadera gestión territorial
            cells_to_keep = list(self.territory_cells)[:max_territory_size]
            self.territory_cells = set(cells_to_keep)


    def get_state_info(self):
        """Retorna información del estado del clan para renderizado."""
        return {
            'id': self.id,
            'size': int(self.size),
            'position': self.position.tolist(),
            'state': self.state,
            'strategy': self.strategy,
            'energy': round(self.energy, 1),
            'morale': round(self.morale, 1),
            'territory_size': len(self.territory_cells),
            'allies': list(self.allies),
            'enemies': list(self.enemies),
            'combat_strength': round(self.size * (self.energy / 100) * self.parameters['aggressiveness'], 1),
            'visual_size': max(3, min(12, np.sqrt(self.size) * 1.5)) # Añadido para sim.js
        }

    def __repr__(self):
        return f"Clan{self.id}(size={self.size:.1f}, pos={self.position.round(1)}, state={self.state})"