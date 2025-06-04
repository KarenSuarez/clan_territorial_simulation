# models/clan.py - Versión simplificada pero funcional
import numpy as np

class Clan:
    def __init__(self, clan_id, initial_size, initial_position, parameters=None):
        self.id = clan_id
        self.size = max(1, int(initial_size))
        self.position = np.array(initial_position, dtype=float)
        
        # Estados básicos
        self.energy = 100.0
        self.morale = 100.0
        self.state = 'foraging'  # foraging, defending, migrating, fighting, resting
        self.strategy = 'cooperative'  # cooperative, aggressive, defensive, exploratory
        
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
            'resource_required_per_individual': 0.1,
            'perception_radius': 5,
            'cooperation_tendency': 0.6,
            'aggressiveness': 0.3,
            'territorial_expansion_rate': 0.2,
            'exploration_tendency': 0.5
        }
        
        if parameters:
            self.parameters.update(parameters)
        
        print(f"Clan {self.id} creado: tamaño={self.size}, posición={self.position}")

    def update_behavior(self, environment, other_clans, dt):
        """Actualiza el comportamiento del clan"""
        try:
            # 1. Percibir entorno
            self._perceive_environment(environment, other_clans)
            
            # 2. Decidir estado
            self._decide_state(environment, other_clans)
            
            # 3. Ejecutar comportamiento según estado
            if self.state == 'foraging':
                self._forage_behavior(environment, dt)
            elif self.state == 'defending':
                self._defend_behavior(environment, dt)
            elif self.state == 'migrating':
                self._migrate_behavior(environment, dt)
            elif self.state == 'fighting':
                self._fight_behavior(other_clans, dt)
            elif self.state == 'resting':
                self._rest_behavior(dt)
            
            # 4. Consumir recursos básicos
            self._consume_resources(environment, dt)
            
            # 5. Actualizar territorio
            self._update_territory()
            
            # 6. Degradar energía
            self.energy = max(0, self.energy - 8 * dt)
            
        except Exception as e:
            print(f"Error en comportamiento del clan {self.id}: {e}")

    def _perceive_environment(self, environment, other_clans):
        """Percibe el entorno y otros clanes"""
        # Actualizar memoria de recursos cercanos
        radius = int(self.parameters['perception_radius'])
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx*dx + dy*dy <= radius*radius:
                    pos = self.position + np.array([dx, dy])
                    pos = environment.get_toroidal_position(pos).astype(int)
                    resource_level = environment.get_resource(pos)
                    self.resource_memory[tuple(pos)] = resource_level

    def _decide_state(self, environment, other_clans):
        """Decide qué estado adoptar"""
        # Evaluar amenazas cercanas
        threats = self._count_nearby_threats(other_clans)
        
        # Evaluar recursos locales
        local_resources = self._evaluate_local_resources(environment)
        
        # Lógica de decisión simple
        if threats > 0 and self.energy > 30:
            if self.size > 8:
                self.state = 'fighting'
            else:
                self.state = 'defending'
        elif local_resources < self.size * 0.3 and self.energy > 20:
            self.state = 'migrating'
        elif self.energy < 25:
            self.state = 'resting'
        else:
            self.state = 'foraging'

    def _count_nearby_threats(self, other_clans):
        """Cuenta amenazas cercanas"""
        threats = 0
        for other_clan in other_clans:
            if other_clan.id != self.id:
                distance = np.linalg.norm(self.position - other_clan.position)
                if distance < 5 and other_clan.size > self.size * 0.8:
                    threats += 1
        return threats

    def _evaluate_local_resources(self, environment):
        """Evalúa recursos en área local"""
        total = 0
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                pos = self.position + np.array([dx, dy])
                pos = environment.get_toroidal_position(pos).astype(int)
                total += environment.get_resource(pos)
        return total

    def _forage_behavior(self, environment, dt):
        """Comportamiento de forrajeo"""
        # Buscar mejor dirección para recursos
        best_direction = self._find_resource_direction(environment)
        
        if np.linalg.norm(best_direction) > 0:
            movement = best_direction * self.parameters['movement_speed'] * dt
            self._move(movement, environment)

    def _defend_behavior(self, environment, dt):
        """Comportamiento defensivo"""
        # Moverse hacia el centro del territorio o quedarse quieto
        if len(self.territory_cells) > 0:
            # Calcular centroide del territorio
            territory_center = np.mean([np.array(cell) for cell in self.territory_cells], axis=0)
            direction = territory_center - self.position
            if np.linalg.norm(direction) > 3:  # Si está lejos del centro
                direction = direction / np.linalg.norm(direction)
                movement = direction * self.parameters['movement_speed'] * 0.5 * dt
                self._move(movement, environment)

    def _migrate_behavior(self, environment, dt):
        """Comportamiento de migración"""
        # Moverse hacia área con mejores recursos
        migration_direction = self._find_migration_direction(environment)
        
        if np.linalg.norm(migration_direction) > 0:
            movement = migration_direction * self.parameters['movement_speed'] * 1.5 * dt
            self._move(movement, environment)

    def _fight_behavior(self, other_clans, dt):
        """Comportamiento de combate"""
        # Buscar enemigo más cercano
        target = None
        min_distance = float('inf')
        
        for other_clan in other_clans:
            if other_clan.id != self.id:
                distance = np.linalg.norm(self.position - other_clan.position)
                if distance < min_distance and distance < 5:
                    target = other_clan
                    min_distance = distance
        
        if target:
            # Moverse hacia el objetivo
            direction = target.position - self.position
            if np.linalg.norm(direction) > 0:
                direction = direction / np.linalg.norm(direction)
                movement = direction * self.parameters['movement_speed'] * 1.2 * dt
                self._move(movement, None)  # No usar entorno para combate
                
                # Combatir si está muy cerca
                if min_distance < 2:
                    self._engage_combat(target, dt)

    def _rest_behavior(self, dt):
        """Comportamiento de descanso"""
        # Recuperar energía sin moverse
        self.energy = min(100, self.energy + 25 * dt)
        self.morale = min(100, self.morale + 10 * dt)

    def _find_resource_direction(self, environment):
        """Encuentra la mejor dirección hacia recursos"""
        best_direction = np.array([0.0, 0.0])
        best_resource = 0
        
        # Probar 8 direcciones
        for angle in np.linspace(0, 2*np.pi, 8, endpoint=False):
            direction = np.array([np.cos(angle), np.sin(angle)])
            test_pos = self.position + direction * 3
            test_pos = environment.get_toroidal_position(test_pos).astype(int)
            
            resource_level = environment.get_resource(test_pos)
            
            # Bonus por exploración
            if tuple(test_pos) not in self.resource_memory:
                resource_level += self.parameters['exploration_tendency'] * 20
            
            if resource_level > best_resource:
                best_resource = resource_level
                best_direction = direction
        
        return best_direction

    def _find_migration_direction(self, environment):
        """Encuentra dirección para migración"""
        best_direction = np.array([0.0, 0.0])
        best_score = -1
        
        # Probar direcciones aleatorias para migración
        for _ in range(6):
            angle = np.random.uniform(0, 2*np.pi)
            direction = np.array([np.cos(angle), np.sin(angle)])
            test_pos = self.position + direction * self.parameters['perception_radius']
            test_pos = environment.get_toroidal_position(test_pos).astype(int)
            
            # Evaluar área objetivo
            area_resources = 0
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    check_pos = test_pos + np.array([dx, dy])
                    check_pos = environment.get_toroidal_position(check_pos).astype(int)
                    area_resources += environment.get_resource(check_pos)
            
            if area_resources > best_score:
                best_score = area_resources
                best_direction = direction
        
        return best_direction

    def _engage_combat(self, enemy, dt):
        """Combate entre clanes"""
        my_strength = self.size * (self.energy / 100) * self.parameters['aggressiveness']
        enemy_strength = enemy.size * (getattr(enemy, 'energy', 50) / 100) * enemy.parameters.get('aggressiveness', 0.3)
        
        total_strength = my_strength + enemy_strength
        if total_strength > 0:
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

    def _consume_resources(self, environment, dt):
        """Consume recursos del entorno"""
        pos = self.position.astype(int)
        needed = self.size * self.parameters['resource_required_per_individual'] * dt
        
        # Eficiencia de grupo
        group_efficiency = 1.0 + (self.parameters['cooperation_tendency'] * 0.3)
        effective_consumption = needed * group_efficiency
        
        consumed = environment.consume(pos, effective_consumption)
        
        # Convertir recursos en energía
        if needed > 0:
            efficiency = consumed / needed
            energy_gain = efficiency * 15 * dt
            self.energy = min(100, self.energy + energy_gain)

    def _move(self, movement_vector, environment):
        """Mueve el clan"""
        if environment:
            new_position = environment.get_toroidal_position(self.position + movement_vector)
        else:
            new_position = self.position + movement_vector
        
        self.position = new_position
        self.movement_history.append(self.position.copy())
        
        # Limitar historia
        if len(self.movement_history) > 20:
            self.movement_history = self.movement_history[-10:]

    def _update_territory(self):
        """Actualiza territorio controlado"""
        # Añadir celdas cercanas al territorio
        expansion_prob = self.parameters['territorial_expansion_rate']
        
        if np.random.random() < expansion_prob:
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx == 0 and dy == 0:
                        continue
                    
                    cell = self.position.astype(int) + np.array([dx, dy])
                    self.territory_cells.add(tuple(cell))
        
        # Limitar tamaño del territorio
        if len(self.territory_cells) > self.size * 2:
            # Remover celdas más lejanas
            distances = [(np.linalg.norm(self.position - np.array(cell)), cell) 
                        for cell in self.territory_cells]
            distances.sort(reverse=True)
            
            # Mantener solo las más cercanas
            keep_count = min(len(distances), self.size * 2)
            self.territory_cells = set([cell for _, cell in distances[:keep_count]])

    def get_state_info(self):
        """Retorna información del estado del clan para renderizado"""
        return {
            'id': self.id,
            'size': int(self.size),
            'position': self.position.tolist(),
            'state': self.state,
            'strategy': self.strategy,
            'energy': round(self.energy, 1),
            'morale': round(getattr(self, 'morale', 50), 1),
            'territory_size': len(self.territory_cells),
            'allies': list(self.allies),
            'enemies': list(self.enemies),
            'combat_strength': round(self.size * (self.energy / 100) * self.parameters['aggressiveness'], 1)
        }

    def __repr__(self):
        return f"Clan{self.id}(size={self.size}, pos={self.position.round(1)}, state={self.state})"