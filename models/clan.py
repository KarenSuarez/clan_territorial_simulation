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

        self.territory_cells = set()
        self.allies = set()
        self.enemies = set()

        self.resource_memory = {}
        self.movement_history = [self.position.copy()]

        self.parameters = {
            'birth_rate': 0.1,
            'natural_death_rate': 0.05,
            'movement_speed': 1.0,
            'resource_required_per_individual': 0.1,
            'perception_radius': 5,
            'cooperation_tendency': 0.6,
            'aggressiveness': 0.3,
            'territorial_expansion_rate': 0.05,
            'exploration_tendency': 0.5
        }

        if parameters:
            self.parameters.update(parameters)
        
        self.rng = None

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
        except Exception as e:
            print(f"Error en comportamiento del clan {self.id}: {e}")

    def _perceive_environment(self, environment, other_clans):
        """Percibe el entorno y otros clanes."""
        radius = int(self.parameters['perception_radius'])
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
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
        self.energy = max(0, self.energy - 10 * dt) 

    def _fight_behavior(self, other_clans, dt):
        """Comportamiento de combate."""
        target = None
        min_distance = float('inf')

        for other_clan in other_clans:
            if other_clan.id != self.id and other_clan.size > 0:
                distance = np.linalg.norm(self.position - other_clan.position)
                if distance < min_distance and distance < 5:
                    target = other_clan
                    min_distance = distance

        if target:
            direction = target.position - self.position
            if np.linalg.norm(direction) > 0:
                direction = direction / np.linalg.norm(direction)
                movement = direction * self.parameters['movement_speed'] * 1.2 * dt
                self._move(movement, None)

            if min_distance < 2: 
                self._engage_combat(target, dt)
        else:
            self.state = 'foraging' 


    def _rest_behavior(self, dt):
        """Comportamiento de descanso."""
        self.energy = min(100, self.energy + 25 * dt)
        self.morale = min(100, self.morale + 10 * dt)
        if self.rng:
            noise = self.rng.random_normal(0, 0.05, size=2) * dt
            self._move(noise, None)


    def _find_resource_direction(self, environment):
        """Encuentra la mejor dirección hacia recursos percibidos."""
        best_direction = np.array([0.0, 0.0])
        max_resource_level = -1.0

        for pos_tuple, resource_level in self.resource_memory.items():
            if resource_level > max_resource_level:
                cell_pos = np.array(pos_tuple)
                direction_vector = cell_pos - self.position

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

        for _ in range(self.parameters['perception_radius'] * 2): 
            if self.rng:
                angle = self.rng.random_uniform(0, 2*np.pi)
            else:
                angle = np.random.uniform(0, 2*np.pi) 

            direction_candidate = np.array([np.cos(angle), np.sin(angle)])
            test_pos = self.position + direction_candidate * self.parameters['perception_radius'] * 1.5 
            test_pos = environment.get_toroidal_position(test_pos).astype(int)

            area_resources = 0
            cells_in_area = 0
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    check_pos = test_pos + np.array([dx, dy])
                    check_pos = environment.get_toroidal_position(check_pos).astype(int)
                    area_resources += environment.get_resource(check_pos)
                    cells_in_area += 1
            
            avg_area_resource = area_resources / cells_in_area if cells_in_area > 0 else 0
            exploration_bonus = 0
            if tuple(test_pos) not in self.resource_memory or self.resource_memory[tuple(test_pos)] < 10: 
                exploration_bonus = self.parameters['exploration_tendency'] * 20

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

        damage_to_enemy = (my_strength / total_strength) * 3 * dt
        damage_to_me = (enemy_strength / total_strength) * 3 * dt

        enemy.size = max(0, enemy.size - damage_to_enemy)
        self.size = max(0, self.size - damage_to_me)

        self.energy = max(0, self.energy - 10 * dt)
        if hasattr(enemy, 'energy'):
            enemy.energy = max(0, enemy.energy - 10 * dt)

        self.morale = max(0, self.morale - 5 * dt)
        enemy.morale = max(0, enemy.morale - 5 * dt)


    def _consume_resources(self, environment, dt):
        """Consume recursos del entorno y actualiza energía y tamaño."""
        pos = self.position.astype(int)
        needed = self.size * self.parameters['resource_required_per_individual'] * dt

        group_efficiency_bonus = self.parameters['cooperation_tendency'] * 0.3
        effective_consumption_rate = self.parameters['resource_required_per_individual'] * (1.0 - group_efficiency_bonus)
        effective_needed = self.size * effective_consumption_rate * dt

        consumed = environment.consume(pos, effective_needed)

        if effective_needed > 0:
            energy_conversion_efficiency = (consumed / effective_needed)
            energy_gain = energy_conversion_efficiency * 15 * dt
            self.energy = min(100, self.energy + energy_gain)
        else:
            self.energy = min(100, self.energy + 2 * dt)

        if self.energy <= 0:
            starvation_mortality = 0.8 * dt  
            deaths_by_starvation = starvation_mortality * self.size
            self.size = max(0, self.size - deaths_by_starvation)
        elif self.energy < 25:
            energy_factor = self.energy / 25.0  
            starvation_mortality = (1.0 - energy_factor) * 0.4 * dt 
            deaths_by_starvation = starvation_mortality * self.size
            self.size = max(0, self.size - deaths_by_starvation)

        if self.energy > 30: 
            current_birth_rate = self.parameters['birth_rate']
            energy_factor_birth = min(1.0, (self.energy - 30) / 70.0) 
            birth_modifier = energy_factor_birth
            births = current_birth_rate * birth_modifier * self.size * dt
            self.size += births

        natural_deaths = self.parameters['natural_death_rate'] * self.size * dt
        self.size = max(0, self.size - natural_deaths)

        self.size = max(0, int(round(self.size)))

        if self.size == 0 and self.energy > 50:
            if self.rng and self.rng.random_float() < 0.1: 
                self.size = 1


    def _move(self, movement_vector, environment):
        """Mueve el clan."""
        if environment:
            new_position = environment.get_toroidal_position(self.position + movement_vector)
        else:
            new_position = self.position + movement_vector

        self.position = new_position
        self.movement_history.append(self.position.copy())

        if len(self.movement_history) > 20: 
            self.movement_history.pop(0) 
    def _update_territory(self):
        """Actualiza territorio controlado."""
        expansion_chance = self.parameters['territorial_expansion_rate'] * (self.energy / 100) * (self.morale / 100)
        
        if self.rng:
            if self.rng.random_float() < expansion_chance:
                dx = self.rng.random_randint(-1, 1)
                dy = self.rng.random_randint(-1, 1)
                if dx != 0 or dy != 0:
                    cell = self.position.astype(int) + np.array([dx, dy])
                    self.territory_cells.add(tuple(cell))
        else:
            if np.random.random() < expansion_chance:
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        if dx == 0 and dy == 0:
                            continue
                        cell = self.position.astype(int) + np.array([dx, dy])
                        self.territory_cells.add(tuple(cell))

        max_territory_size = self.size * 5 
        if len(self.territory_cells) > max_territory_size:

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