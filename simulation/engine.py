# simulation/engine.py - Motor simplificado pero funcional
import numpy as np

class SimulationEngine:
    def __init__(self, environment, initial_clans, simulation_mode=None, dt=0.2, seed=None):
        self.environment = environment
        self.clans = list(initial_clans)
        self.time = 0.0
        self.dt = dt
        self.simulation_mode = simulation_mode
        self.seed = seed
        self.step_count = 0
        
        # Historia básica
        self.population_history = []
        
        if seed is not None:
            np.random.seed(seed)
        
        print(f"Motor de simulación inicializado:")
        print(f"  - {len(self.clans)} clanes")
        print(f"  - Entorno: {self.environment.grid_size}")
        print(f"  - dt: {self.dt}")

    def step(self):
        """Ejecuta un paso completo de simulación"""
        try:
            self.step_count += 1
            dt = self.dt
            
            print(f"\n=== Paso {self.step_count} (t={self.time:.2f}) ===")
            
            # 1. Regenerar recursos del entorno
            self.environment.regenerate(dt)
            
            # 2. Actualizar comportamiento de cada clan
            for clan in self.clans[:]:  # Usar slice para evitar problemas con modificaciones
                if clan.size > 0:
                    try:
                        clan.update_behavior(self.environment, self.clans, dt)
                    except Exception as e:
                        print(f"Error actualizando clan {clan.id}: {e}")
            
            # 3. Procesar interacciones entre clanes cercanos
            self._process_interactions(dt)
            
            # 4. Aplicar dinámicas poblacionales
            self._apply_population_dynamics(dt)
            
            # 5. Remover clanes extintos
            initial_count = len(self.clans)
            self.clans = [clan for clan in self.clans if clan.size > 0]
            if len(self.clans) < initial_count:
                print(f"Se extinguieron {initial_count - len(self.clans)} clanes")
            
            # 6. Registrar métricas
            self._record_metrics()
            
            # 7. Avanzar tiempo
            self.time += dt
            
            print(f"Clanes activos: {len(self.clans)}")
            for clan in self.clans:
                print(f"  {clan}: energía={clan.energy:.1f}")
                
        except Exception as e:
            print(f"Error en paso de simulación: {e}")
            import traceback
            traceback.print_exc()

    def _process_interactions(self, dt):
        """Procesa interacciones entre clanes cercanos"""
        interaction_radius = 3.0
        
        for i, clan1 in enumerate(self.clans):
            for j, clan2 in enumerate(self.clans[i+1:], i+1):
                distance = np.linalg.norm(clan1.position - clan2.position)
                
                if distance <= interaction_radius:
                    self._handle_interaction(clan1, clan2, distance, dt)

    def _handle_interaction(self, clan1, clan2, distance, dt):
        """Maneja interacción específica entre dos clanes"""
        interaction_strength = max(0.1, 1.0 - (distance / 3.0))
        
        # Determinar tipo de interacción basado en estrategias y tamaños
        if clan1.strategy == 'cooperative' and clan2.strategy == 'cooperative':
            # Interacción cooperativa
            if np.random.random() < 0.1:  # 10% chance de formar alianza
                clan1.allies.add(clan2.id)
                clan2.allies.add(clan1.id)
            
            # Bonus de moral por cooperación
            clan1.morale = min(100, clan1.morale + 2 * interaction_strength * dt)
            clan2.morale = min(100, clan2.morale + 2 * interaction_strength * dt)
            
        elif (clan1.strategy == 'aggressive' or clan2.strategy == 'aggressive') and distance < 2:
            # Interacción agresiva/combate
            if clan1.energy > 30 and clan2.energy > 30:
                self._combat_interaction(clan1, clan2, dt)
        
        else:
            # Interacción neutral - competencia por recursos
            if distance < 1.5:
                self._resource_competition(clan1, clan2, dt)

    def _combat_interaction(self, clan1, clan2, dt):
        """Maneja combate entre clanes"""
        # Calcular fuerzas de combate
        strength1 = clan1.size * (clan1.energy / 100) * clan1.parameters.get('aggressiveness', 0.5)
        strength2 = clan2.size * (clan2.energy / 100) * clan2.parameters.get('aggressiveness', 0.5)
        
        total_strength = strength1 + strength2
        if total_strength > 0:
            # Daño proporcional a la fuerza relativa
            damage1 = (strength2 / total_strength) * 4 * dt
            damage2 = (strength1 / total_strength) * 4 * dt
            
            # Aplicar daño
            clan1.size = max(0, clan1.size - damage1)
            clan2.size = max(0, clan2.size - damage2)
            
            # Costo de energía por combate
            clan1.energy = max(0, clan1.energy - 15 * dt)
            clan2.energy = max(0, clan2.energy - 15 * dt)
            
            # Convertir en enemigos
            clan1.enemies.add(clan2.id)
            clan2.enemies.add(clan1.id)
            clan1.allies.discard(clan2.id)
            clan2.allies.discard(clan1.id)
            
            print(f"Combate: Clan {clan1.id} vs Clan {clan2.id}")

    def _resource_competition(self, clan1, clan2, dt):
        """Maneja competencia por recursos"""
        # El clan más grande obtiene ventaja en la competencia
        advantage1 = clan1.size / (clan1.size + clan2.size)
        advantage2 = clan2.size / (clan1.size + clan2.size)
        
        # Redistribuir energía según ventaja
        energy_transfer = 5 * dt
        if advantage1 > advantage2:
            clan1.energy = min(100, clan1.energy + energy_transfer * advantage1)
            clan2.energy = max(0, clan2.energy - energy_transfer * advantage2)
        else:
            clan2.energy = min(100, clan2.energy + energy_transfer * advantage2)
            clan1.energy = max(0, clan1.energy - energy_transfer * advantage1)

    def _apply_population_dynamics(self, dt):
        """Aplica dinámicas poblacionales básicas"""
        for clan in self.clans:
            if clan.size <= 0:
                continue
                
            try:
                # Tasas base
                birth_rate = clan.parameters.get('birth_rate', 0.1)
                death_rate = clan.parameters.get('natural_death_rate', 0.05)
                
                # Modificadores
                energy_factor = clan.energy / 100.0
                resource_factor = self._get_local_resource_factor(clan)
                
                # Calcular tasas efectivas
                effective_birth_rate = birth_rate * energy_factor * resource_factor
                effective_death_rate = death_rate * (2.0 - energy_factor)
                
                # Aplicar cambio poblacional
                net_rate = effective_birth_rate - effective_death_rate
                population_change = net_rate * clan.size * dt
                
                clan.size += population_change
                clan.size = max(0, int(round(clan.size)))
                
            except Exception as e:
                print(f"Error en dinámica poblacional del clan {clan.id}: {e}")

    def _get_local_resource_factor(self, clan):
        """Calcula factor de recursos locales para un clan"""
        total_resources = 0
        cell_count = 0
        
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                pos = clan.position + np.array([dx, dy])
                pos = self.environment.get_toroidal_position(pos).astype(int)
                total_resources += self.environment.get_resource(pos)
                cell_count += 1
        
        avg_resource = total_resources / cell_count if cell_count > 0 else 0
        required_per_individual = clan.parameters.get('resource_required_per_individual', 0.1) * 100
        
        return min(1.5, avg_resource / (clan.size * required_per_individual)) if clan.size > 0 else 1.0

    def _record_metrics(self):
        """Registra métricas básicas del sistema"""
        total_population = sum(clan.size for clan in self.clans)
        avg_energy = np.mean([clan.energy for clan in self.clans]) if self.clans else 0
        
        self.population_history.append({
            'step': self.step_count,
            'time': self.time,
            'total_population': total_population,
            'clan_count': len(self.clans),
            'avg_energy': avg_energy
        })
        
        # Limitar historia
        if len(self.population_history) > 500:
            self.population_history = self.population_history[-250:]

    def get_simulation_state(self):
        """Obtiene el estado actual de la simulación"""
        try:
            state = {
                'time': self.time,
                'step': self.step_count,
                'clans': [],
                'resource_grid': self.environment.grid.tolist(),
                'system_metrics': {
                    'total_population': sum(clan.size for clan in self.clans),
                    'active_clans': len(self.clans),
                    'avg_energy': np.mean([clan.energy for clan in self.clans]) if self.clans else 0
                }
            }
            
            # Información de cada clan
            for clan in self.clans:
                clan_data = clan.get_state_info()
                state['clans'].append(clan_data)
            
            return state
            
        except Exception as e:
            print(f"Error obteniendo estado de simulación: {e}")
            return {
                'time': self.time,
                'step': self.step_count,
                'clans': [],
                'resource_grid': [],
                'error': str(e)
            }

    def run_step(self):
        """Alias para compatibilidad"""
        self.step()

    def __repr__(self):
        return f"SimulationEngine(t={self.time:.2f}, clanes={len(self.clans)})"