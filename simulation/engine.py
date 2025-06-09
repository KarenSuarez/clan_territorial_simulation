import numpy as np
from models.environment import Environment 
from models.clan import Clan 

class SimulationEngine:
    def __init__(self, environment: Environment, initial_clans: list, simulation_mode, dt: float = 0.2, seed: int = None):
        self.environment = environment
        self.clans = list(initial_clans)
        self.time = 0.0
        self.dt = dt
        self.simulation_mode = simulation_mode
        self.seed = seed
        self.step_count = 0
        self.max_steps = 500

        self.population_history = []
        self.resource_history = []

        print(f"Motor de simulación inicializado:")
        print(f" - {len(self.clans)} clanes")
        print(f" - Entorno: {self.environment.grid_size}")
        print(f" - dt: {self.dt}")
        print(f" - Modo: {type(self.simulation_mode).__name__}, Semilla: {self.seed}")

    def step(self):
        """Ejecuta un paso completo de simulación."""
        try:
            self.step_count += 1
            dt = self.dt

            # 1. Regenerar recursos del entorno
            self.environment.regenerate(dt)

            # 2. Actualizar comportamiento de cada clan usando el modo
            for clan in self.clans[:]:
                if clan.size > 0:
                    try:
                        self.simulation_mode.apply_clan_behavior(clan, self.environment, dt)
                        clan._consume_resources(self.environment, dt)

                        if clan.energy > 0:
                            energy_decay = min(clan.energy, 3 * dt) 
                            clan.energy = max(0, clan.energy - energy_decay)

                        if clan.size <= 0:
                            print(f"💀 Clan {clan.id} se ha extinguido (tamaño: {clan.size})")

                    except Exception as e:
                        print(f"Error actualizando clan {clan.id}: {e}")

            # 3. Procesar interacciones entre clanes cercanos
            self._process_interactions(dt)

            # 4. Aplicar dinámicas poblacionales adicionales si es necesario
            self._apply_population_dynamics(dt)

            # 5. Remover clanes extintos
            initial_clan_count = len(self.clans)
            self.clans = [clan for clan in self.clans if clan.size > 0]
            if len(self.clans) < initial_clan_count:
                extinct_count = initial_clan_count - len(self.clans)
                print(f"🪦 {extinct_count} clan(es) removido(s) por extinción")
            
            # 6. Actualizar territorio para todos los clanes restantes
            for clan in self.clans:
                clan._update_territory()

            # 7. Registrar métricas
            self._record_metrics()

            # 8. Avanzar tiempo
            self.time += dt

            if self.step_count % 50 == 0:
                total_pop = sum(clan.size for clan in self.clans)
                avg_energy = np.mean([clan.energy for clan in self.clans]) if self.clans else 0
                print(f"📊 Paso {self.step_count}: {len(self.clans)} clanes, {total_pop:.1f} población, {avg_energy:.1f}% energía promedio")

        except Exception as e:
            print(f"Error en paso de simulación: {e}")
            import traceback
            traceback.print_exc()

    def _process_interactions(self, dt):
        """Procesa interacciones entre clanes cercanos."""
        interaction_radius = 5.0

        rng = self.simulation_mode.rng 

        for i, clan1 in enumerate(self.clans):
            for j, clan2 in enumerate(self.clans[i+1:], i+1):
                distance = np.linalg.norm(clan1.position - clan2.position)

                if distance <= interaction_radius:
                    self._handle_interaction(clan1, clan2, distance, dt, rng)

    def _handle_interaction(self, clan1, clan2, distance, dt, rng):
        """Maneja interacción específica entre dos clanes."""
        interaction_radius = 5.0
        interaction_strength = max(0.1, 1.0 - (distance / interaction_radius))

        if clan1.strategy == 'cooperative' and clan2.strategy == 'cooperative':
            if rng.random_float() < clan1.parameters.get('cooperation_tendency', 0.6) and \
               rng.random_float() < clan2.parameters.get('cooperation_tendency', 0.6):
                if rng.random_float() < 0.2:
                    clan1.allies.add(clan2.id)
                    clan2.allies.add(clan1.id)


            clan1.morale = min(100, clan1.morale + 2 * interaction_strength * dt)
            clan2.morale = min(100, clan2.morale + 2 * interaction_strength * dt)

        elif (clan1.strategy == 'aggressive' or clan2.strategy == 'aggressive') or \
             (clan1.enemies.intersection({clan2.id}) or clan2.enemies.intersection({clan1.id})): # Si son enemigos
            # Interacción agresiva/combate
            if distance < 2.5: # Reducir distancia para combate directo
                if clan1.energy > 20 and clan2.energy > 20: # Requiere energía para combatir
                    self._combat_interaction(clan1, clan2, dt, rng)

        else: # Interacción neutral - competencia por recursos
            if distance < 1.5:
                self._resource_competition(clan1, clan2, dt)


    def _combat_interaction(self, clan1, clan2, dt, rng):
        """Maneja combate entre clanes."""
        aggressiveness1 = clan1.parameters.get('aggressiveness', 0.5)
        aggressiveness2 = clan2.parameters.get('aggressiveness', 0.5)

        strength1 = clan1.size * (clan1.energy / 100) * aggressiveness1
        strength2 = clan2.size * (clan2.energy / 100) * aggressiveness2

        strength1 *= (1 + rng.random_normal(0, 0.1))
        strength2 *= (1 + rng.random_normal(0, 0.1))

        total_strength = strength1 + strength2
        if total_strength <= 0: return

        damage1 = (strength2 / total_strength) * 5 * dt
        damage2 = (strength1 / total_strength) * 5 * dt

        clan1.size = max(0, clan1.size - damage1)
        clan2.size = max(0, clan2.size - damage2)

        clan1.energy = max(0, clan1.energy - 20 * dt)
        clan2.energy = max(0, clan2.energy - 20 * dt)

        clan1.enemies.add(clan2.id)
        clan2.enemies.add(clan1.id)
        clan1.allies.discard(clan2.id)
        clan2.allies.discard(clan1.id)
  

    def _resource_competition(self, clan1, clan2, dt):
        """Maneja competencia por recursos (no es combate directo)."""
        score1 = clan1.size * (clan1.energy / 100)
        score2 = clan2.size * (clan2.energy / 100)

        total_score = score1 + score2
        if total_score <= 0: return

        share1 = score1 / total_score
        share2 = score2 / total_score

        energy_penalty = 10 * dt
        clan1.energy = max(0, clan1.energy - energy_penalty * share2)
        clan2.energy = max(0, clan2.energy - energy_penalty * share1)

    def _apply_population_dynamics(self, dt):
        """Aplica dinámicas poblacionales básicas."""

        for clan in self.clans:
            if clan.size <= 0:
                continue
            pass


    def _record_metrics(self):
        """Registra métricas básicas del sistema."""
        total_population = sum(clan.size for clan in self.clans)
        avg_energy = np.mean([clan.energy for clan in self.clans]) if self.clans else 0
        total_resources = self.environment.get_total_resources()

        self.population_history.append(total_population)
        self.resource_history.append(total_resources)

        if len(self.population_history) > 1000:
            self.population_history = self.population_history[-500:] 
            self.resource_history = self.resource_history[-500:]


    def get_simulation_state(self):
        """Obtiene el estado actual de la simulación para el frontend."""
        try:
            clans_data = [clan.get_state_info() for clan in self.clans]

            resource_grid_data = self.environment.grid.tolist()

            state = {
                'time': self.time,
                'step': self.step_count,
                'clans': clans_data,
                'resource_grid': resource_grid_data,
                'system_metrics': {
                    'total_population': sum(clan.size for clan in self.clans),
                    'active_clans': len(self.clans),
                    'avg_energy': np.mean([clan.energy for clan in self.clans]) if self.clans else 0,
                    'total_resources': self.environment.get_total_resources()
                }
            }
            return state

        except Exception as e:
            print(f"Error obteniendo estado de simulación del motor: {e}")
            import traceback
            traceback.print_exc()
            return {
                'time': self.time,
                'step': self.step_count,
                'clans': [],
                'resource_grid': [],
                'error': str(e),
                'system_metrics': {}
            }

    def run_step(self):
        """Alias para compatibilidad."""
        self.step()

    def __repr__(self):
        return f"SimulationEngine(t={self.time:.2f}, clanes={len(self.clans)})"