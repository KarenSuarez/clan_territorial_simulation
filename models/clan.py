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
            'exploration_tendency': 0.5,
            'starvation_mortality_rate': 0.1 # Nuevo parámetro para la mortalidad por inanición
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
        try:
            self._perceive_environment(environment, other_clans)
            self._decide_state(environment, other_clans)
            
            # La ejecución del comportamiento específico (_forage_behavior, etc.)
            # ahora se deja al SimulationMode que llama a este método.
            # Sin embargo, el consumo de recursos y la degradación de energía son inherentes a Clan
            self._apply_energy_consumption_and_population_dynamics(environment, dt) # Unificar aquí

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

        # Lógica de decisión mejorada
        if self.energy < 20 and self.size > 0: # Prioridad máxima: descansar si hay poca energía
            self.state = 'resting'
        elif threats > 0 and self.energy > 30: # Combatir/defender si hay amenaza y energía para ello
            if self.size > 8:
                self.state = 'fighting'
            else:
                self.state = 'defending'
        elif local_resources < self.size * self.parameters['resource_required_per_individual'] * 10 and self.energy > 40:
            # Migrar si los recursos locales son escasos y aún hay energía suficiente para buscar
            self.state = 'migrating'
        else: # Por defecto, forrajear
            self.state = 'foraging'

    def _count_nearby_threats(self, other_clans):
        """Cuenta amenazas cercanas."""
        threats = 0
        for other_clan in other_clans:
            if other_clan.id != self.id and other_clan.size > 0:
                distance = np.linalg.norm(self.position - other_clan.position)
                # Considerar amenaza si está cerca y es más grande o igual
                if distance < self.parameters['perception_radius'] / 2 and other_clan.size >= self.size * 0.8:
                    threats += 1
        return threats

    def _evaluate_local_resources(self, environment):
        """Evalúa recursos en área local (promedio de recursos percibidos)."""
        if not self.resource_memory:
            return 0
        
        # Filtrar solo recursos válidos y calcular el promedio
        valid_resources = [res for res in self.resource_memory.values() if res is not None and res > 0]
        return sum(valid_resources) / len(valid_resources) if valid_resources else 0


    def _forage_behavior(self, environment, dt):
        """Comportamiento de forrajeo."""
        best_direction = self._find_resource_direction(environment)
        if np.linalg.norm(best_direction) > 0:
            movement = best_direction * self.parameters['movement_speed'] * dt
            self._move(movement, environment)
        # Consumir recursos se maneja en _apply_energy_consumption_and_population_dynamics


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
            # Esta decisión se hace en _decide_state, así que no es necesaria aquí.
            pass


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
        # Priorizar celdas con más recursos, con un sesgo hacia celdas no tan cerca
        # para evitar quedarse atascado en un mínimo local.
        
        # Percibir una pequeña área alrededor para suavizar el gradiente
        perceived_cells_data = []
        radius = int(self.parameters['perception_radius'])
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if np.sqrt(dx*dx + dy*dy) <= radius:
                    pos = self.position + np.array([dx, dy])
                    toroidal_pos = environment.get_toroidal_position(pos).astype(int)
                    resource_level = environment.get_resource(toroidal_pos)
                    distance = np.linalg.norm(self.position - toroidal_pos) # Distancia real a la celda
                    if resource_level > 0: # Solo considerar celdas con recursos
                         perceived_cells_data.append((resource_level, toroidal_pos, distance))
        
        # Ordenar por nivel de recurso, y luego por distancia (más cerca es mejor)
        perceived_cells_data.sort(key=lambda x: (x[0], -x[2]), reverse=True) # Max resource, then min distance

        if perceived_cells_data:
            # Tomar la mejor celda
            best_resource_level, best_cell_pos, _ = perceived_cells_data[0]
            
            direction_vector = np.array(best_cell_pos) - self.position
            # Ajustar para toroidalidad si el movimiento cruza el borde
            # Esto es un poco más complejo si la dirección es larga
            # Una forma simple para toroidalidad: si la distancia es > GRID_SIZE/2, ir por el otro lado
            grid_size = environment.grid_size[0] # Asumimos grid cuadrado
            if abs(direction_vector[0]) > grid_size / 2:
                direction_vector[0] -= np.sign(direction_vector[0]) * grid_size
            if abs(direction_vector[1]) > grid_size / 2:
                direction_vector[1] -= np.sign(direction_vector[1]) * grid_size
            
            norm = np.linalg.norm(direction_vector)
            if norm > 0:
                best_direction = direction_vector / norm
            
            # Pequeño factor de exploración si la mejor celda es muy conocida y no muy rica
            if self.rng and self.rng.random_float() < self.parameters['exploration_tendency'] and best_resource_level < 50:
                 best_direction = self.rng.random_normal(0, 1, size=2)
                 norm_exp = np.linalg.norm(best_direction)
                 if norm_exp > 0:
                     best_direction /= norm_exp
        
        return best_direction


    def _find_migration_direction(self, environment):
        """Encuentra dirección para migración, buscando áreas con altos recursos no explorados."""
        best_direction = np.array([0.0, 0.0])
        best_score = -1.0

        # Para migración, buscar áreas con recursos altos y posiblemente poco exploradas
        # Usaremos una serie de puntos de prueba aleatorios
        num_test_points = 10 # Más intentos para mejor búsqueda
        if self.rng:
            test_angles = self.rng.random_uniform(0, 2*np.pi, num_test_points)
        else:
            test_angles = np.random.uniform(0, 2*np.pi, num_test_points) # Fallback

        for angle in test_angles:
            direction_candidate = np.array([np.cos(angle), np.sin(angle)])
            # Probar un punto más lejano para migración
            test_pos = self.position + direction_candidate * self.parameters['perception_radius'] * 2 
            test_pos = environment.get_toroidal_position(test_pos).astype(int)

            # Evaluar recursos en el área objetivo del test_pos
            area_resources = 0
            cells_in_area = 0
            # Evaluar un cuadrado de 5x5 alrededor del punto de prueba
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


    def _apply_energy_consumption_and_population_dynamics(self, environment, dt):
        """
        Consumir recursos del entorno, actualizar energía y aplicar dinámicas poblacionales
        incluyendo mortalidad por inanición.
        """
        pos = self.position.astype(int)
        
        # Calcular recursos necesarios
        needed = self.size * self.parameters['resource_required_per_individual'] * dt

        # Aplicar eficiencia de grupo/cooperación en el consumo
        group_efficiency_factor = 1.0 - (self.parameters['cooperation_tendency'] * 0.3)
        effective_needed = needed * group_efficiency_factor # Menos necesario si hay cooperación
        
        # Consumir del entorno
        consumed_resources = environment.consume(pos, effective_needed)

        # Ganancia de energía
        if effective_needed > 0:
            energy_conversion_efficiency = (consumed_resources / effective_needed) # Cuánto % de lo necesario se consumió
            energy_gain = energy_conversion_efficiency * 20 * dt # Factor de ganancia de energía (20 es arbitrario)
            self.energy = min(100, self.energy + energy_gain)
        
        # Degradación de energía por tiempo y actividad (si no está descansando)
        if self.state != 'resting':
            self.energy = max(0, self.energy - 8 * dt)
        else: # Si está descansando, la degradación es menor (o nula)
            self.energy = min(100, self.energy + 5 * dt) # Pequeña ganancia incluso si no forrajea

        # Aplicar mortalidad por inanición si la energía es muy baja
        if self.energy <= 10: # Umbral bajo de energía
            starvation_mortality_rate = self.parameters['starvation_mortality_rate'] * (1 - self.energy / 10) # Mayor si energía es 0
            population_loss_starvation = starvation_mortality_rate * self.size * dt
            self.size = max(0, self.size - population_loss_starvation)

        # Dinámica poblacional (nacimientos y muertes naturales)
        current_birth_rate = self.parameters['birth_rate']
        current_death_rate = self.parameters['natural_death_rate']

        # Modificadores de natalidad y mortalidad basados en energía
        # Más energía = más nacimientos, menos muertes
        # Menos energía = menos nacimientos, más muertes
        energy_factor_for_growth = self.energy / 100.0 # 0 a 1
        
        # Tasa de natalidad: aumenta con la energía (ej. si energía > 60)
        effective_birth_rate = current_birth_rate * max(0, (energy_factor_for_growth - 0.6) * 2.5) # Factor que activa nacimientos
        
        # Tasa de mortalidad: aumenta si la energía es baja (ej. si energía < 40)
        effective_death_rate = current_death_rate * max(1, (0.4 - energy_factor_for_growth) * 2.5) # Factor que aumenta mortalidad

        population_change = (effective_birth_rate - effective_death_rate) * self.size * dt
        self.size += population_change
        self.size = max(0, int(round(self.size))) # Redondear y asegurar que no sea negativo


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
        # La expansión se vuelve más difícil si el territorio ya es grande
        territory_pressure_factor = 1.0 # 1.0 - (len(self.territory_cells) / (self.size * 5 + 1e-6)) # Penalizar territorios grandes
        
        expansion_chance = self.parameters['territorial_expansion_rate'] * (self.energy / 100) * (self.morale / 100) * territory_pressure_factor
        
        if self.rng:
            if self.rng.random_float() < expansion_chance:
                # Reclamar una celda adyacente aleatoria si hay RNG
                # Priorizar celdas que no estén ya en el territorio
                possible_new_cells = []
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        if dx == 0 and dy == 0:
                            continue
                        cell = self.position.astype(int) + np.array([dx, dy])
                        cell_tuple = tuple(cell)
                        if cell_tuple not in self.territory_cells:
                            possible_new_cells.append(cell_tuple)
                
                if possible_new_cells:
                    chosen_cell = self.rng.random_choice(possible_new_cells)
                    self.territory_cells.add(chosen_cell)
        else: # Fallback sin RNG (debería ser eliminado en Solicitud 2)
            if np.random.random() < expansion_chance:
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        if dx == 0 and dy == 0:
                            continue
                        cell = self.position.astype(int) + np.array([dx, dy])
                        self.territory_cells.add(tuple(cell))


        # Limitar tamaño del territorio a algo razonable basado en el tamaño del clan
        max_territory_size = int(self.size * 5) + 1 # Cada individuo puede controlar hasta 5 celdas
        if len(self.territory_cells) > max_territory_size:
            # Remover celdas más lejanas o antiguas si el territorio es demasiado grande
            # Para simplificar, remover al azar hasta el tamaño deseado.
            if self.rng:
                cells_to_remove_count = len(self.territory_cells) - max_territory_size
                cells_list = list(self.territory_cells)
                cells_to_remove = self.rng.random_choice(cells_list, size=cells_to_remove_count, replace=False)
                for cell in cells_to_remove:
                    self.territory_cells.discard(cell)
            else: # Fallback sin RNG
                # Implementación simple: convertir a lista y truncar
                cells_list = list(self.territory_cells)
                self.territory_cells = set(cells_list[:max_territory_size])


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