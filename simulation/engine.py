# simulation/engine.py - Motor de simulación con integración de modos

import numpy as np
from models.environment import Environment # Asegurarse de importar Environment si no lo está
from models.clan import Clan # Asegurarse de importar Clan si no lo está

class SimulationEngine:
    def __init__(self, environment: Environment, initial_clans: list, simulation_mode, dt: float = 0.2, seed: int = None):
        self.environment = environment
        self.clans = list(initial_clans)
        self.time = 0.0
        self.dt = dt
        self.simulation_mode = simulation_mode # Aquí se recibe la instancia del modo
        self.seed = seed # Esta semilla debería ser la misma que la del RNG del modo
        self.step_count = 0
        self.max_steps = 500 # Se puede actualizar desde app.py

        self.population_history = []
        self.resource_history = [] # Añadir historial de recursos para gráficos

        # El RNG ahora está centralizado en el objeto simulation_mode
        # No se necesita np.random.seed(seed) aquí si el modo lo maneja.

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

            # print(f"\n=== Paso {self.step_count} (t={self.time:.2f}) ===")

            # 1. Regenerar recursos del entorno
            # La regeneración ahora usa el RNG del modo si el Environment lo tiene (ver Solicitud 2)
            self.environment.regenerate(dt)

            # 2. Actualizar comportamiento de cada clan usando el modo
            for clan in self.clans[:]:
                if clan.size > 0:
                    try:
                        # El modo de simulación dicta cómo el clan se comporta
                        self.simulation_mode.apply_clan_behavior(clan, self.environment, dt)
                        # Consumir recursos básicos y degradar energía se mantiene en el clan
                        clan._consume_resources(self.environment, dt) 
                        clan.energy = max(0, clan.energy - 8 * dt) # Degradación de energía por tiempo

                    except Exception as e:
                        print(f"Error actualizando clan {clan.id}: {e}")

            # 3. Procesar interacciones entre clanes cercanos
            self._process_interactions(dt)

            # 4. Aplicar dinámicas poblacionales
            self._apply_population_dynamics(dt)

            # 5. Remover clanes extintos
            self.clans = [clan for clan in self.clans if clan.size > 0]
            
            # 6. Actualizar territorio para todos los clanes restantes
            for clan in self.clans:
                clan._update_territory() # Asegurarse de que el clan actualice su propio territorio

            # 7. Registrar métricas
            self._record_metrics()

            # 8. Avanzar tiempo
            self.time += dt

            # print(f"Clanes activos: {len(self.clans)}")
            # for clan in self.clans:
            #     print(f" {clan}: energía={clan.energy:.1f}")

        except Exception as e:
            print(f"Error en paso de simulación: {e}")
            import traceback
            traceback.print_exc()

    def _process_interactions(self, dt):
        """Procesa interacciones entre clanes cercanos."""
        interaction_radius = 5.0 # Aumentar radio de interacción para que sea más notable

        # Usar el RNG del modo para decisiones aleatorias en interacciones
        rng = self.simulation_mode.rng 

        for i, clan1 in enumerate(self.clans):
            for j, clan2 in enumerate(self.clans[i+1:], i+1):
                distance = np.linalg.norm(clan1.position - clan2.position)

                if distance <= interaction_radius:
                    self._handle_interaction(clan1, clan2, distance, dt, rng) # Pasar RNG

    def _handle_interaction(self, clan1, clan2, distance, dt, rng):
        """Maneja interacción específica entre dos clanes."""
        interaction_strength = max(0.1, 1.0 - (distance / interaction_radius)) # Normalizar fuerza

        # Determinar tipo de interacción basado en estrategias y tamaños
        if clan1.strategy == 'cooperative' and clan2.strategy == 'cooperative':
            if rng.random_float() < clan1.parameters.get('cooperation_tendency', 0.6) and \
               rng.random_float() < clan2.parameters.get('cooperation_tendency', 0.6):
                # Mayor probabilidad de formar alianza
                if rng.random_float() < 0.2: # 20% chance de formar alianza si ambos son cooperativos
                    clan1.allies.add(clan2.id)
                    clan2.allies.add(clan1.id)
                    # print(f"Alianza formada entre Clan {clan1.id} y Clan {clan2.id}")
            
            # Bonus de moral por cooperación
            clan1.morale = min(100, clan1.morale + 2 * interaction_strength * dt)
            clan2.morale = min(100, clan2.morale + 2 * interaction_strength * dt)

        elif (clan1.strategy == 'aggressive' or clan2.strategy == 'aggressive') or \
             (clan1.enemies.intersection({clan2.id}) or clan2.enemies.intersection({clan1.id})): # Si son enemigos
            # Interacción agresiva/combate
            if distance < 2.5: # Reducir distancia para combate directo
                if clan1.energy > 20 and clan2.energy > 20: # Requiere energía para combatir
                    self._combat_interaction(clan1, clan2, dt, rng) # Pasar RNG

        else: # Interacción neutral - competencia por recursos
            if distance < 1.5:
                self._resource_competition(clan1, clan2, dt)


    def _combat_interaction(self, clan1, clan2, dt, rng):
        """Maneja combate entre clanes."""
        # Calcular fuerzas de combate
        # Usar agresividad del clan, tamaño y energía
        aggressiveness1 = clan1.parameters.get('aggressiveness', 0.5)
        aggressiveness2 = clan2.parameters.get('aggressiveness', 0.5)

        strength1 = clan1.size * (clan1.energy / 100) * aggressiveness1
        strength2 = clan2.size * (clan2.energy / 100) * aggressiveness2

        # Pequeño factor aleatorio en el combate para ambos modos
        strength1 *= (1 + rng.random_normal(0, 0.1))
        strength2 *= (1 + rng.random_normal(0, 0.1))

        total_strength = strength1 + strength2
        if total_strength <= 0: return

        # Daño proporcional a la fuerza relativa
        damage1 = (strength2 / total_strength) * 5 * dt # Clan1 recibe daño del clan2
        damage2 = (strength1 / total_strength) * 5 * dt # Clan2 recibe daño del clan1

        # Aplicar daño
        clan1.size = max(0, clan1.size - damage1)
        clan2.size = max(0, clan2.size - damage2)

        # Costo de energía por combate
        clan1.energy = max(0, clan1.energy - 20 * dt)
        clan2.energy = max(0, clan2.energy - 20 * dt)

        # Establecer como enemigos (si no lo eran ya)
        clan1.enemies.add(clan2.id)
        clan2.enemies.add(clan1.id)
        clan1.allies.discard(clan2.id) # Romper alianzas si entran en combate
        clan2.allies.discard(clan1.id)
        # print(f"Combate: Clan {clan1.id} (pop: {clan1.size:.1f}) vs Clan {clan2.id} (pop: {clan2.size:.1f})")

    def _resource_competition(self, clan1, clan2, dt):
        """Maneja competencia por recursos (no es combate directo)."""
        # El clan con más energía y tamaño tiene ventaja
        score1 = clan1.size * (clan1.energy / 100)
        score2 = clan2.size * (clan2.energy / 100)

        total_score = score1 + score2
        if total_score <= 0: return

        # Proporción de energía obtenida del recurso en disputa
        share1 = score1 / total_score
        share2 = score2 / total_score

        # Simular que ambos consumen del mismo recurso pero con eficiencia dictada por su share
        # Asumimos que environment.consume ya fue llamado por el comportamiento individual de cada clan
        # Esto solo simula una redistribución o penalización si compiten en la misma celda
        
        # Una pequeña penalización si ambos están en la misma celda de recurso
        energy_penalty = 10 * dt
        clan1.energy = max(0, clan1.energy - energy_penalty * share2) # Pierde energía por la presencia del otro
        clan2.energy = max(0, clan2.energy - energy_penalty * share1)

    def _apply_population_dynamics(self, dt):
        """Aplica dinámicas poblacionales básicas."""
        # Se asume que las ecuaciones se aplican por el Clan mismo o un módulo de dinámica de población.
        # Aquí, simplemente actualizamos el tamaño del clan basado en sus tasas internas.
        for clan in self.clans:
            if clan.size <= 0:
                continue
            
            # El Clan ya maneja su propia dinámica poblacional en update_behavior
            # Solo necesitamos asegurarnos de que el dt se use y las ecuaciones sean correctas.
            # clan.update_population(dt) # Si tuviéramos un método específico
            
            # Por ahora, la lógica de crecimiento/decrecimiento simple de app.py se movió a Clan
            # y se refinará en Solicitud 4 para usar equations.py
            # Esta lógica ya está en clan.py en _consume_resources
            pass


    def _record_metrics(self):
        """Registra métricas básicas del sistema."""
        total_population = sum(clan.size for clan in self.clans)
        avg_energy = np.mean([clan.energy for clan in self.clans]) if self.clans else 0
        total_resources = self.environment.get_total_resources()

        self.population_history.append(total_population)
        self.resource_history.append(total_resources) # Registrar recursos

        # Limitar historia para evitar un crecimiento excesivo
        if len(self.population_history) > 1000: # Por ejemplo, últimos 1000 pasos
            self.population_history = self.population_history[-500:] # Mantener 500 para un buen historial
            self.resource_history = self.resource_history[-500:]


    def get_simulation_state(self):
        """Obtiene el estado actual de la simulación para el frontend."""
        try:
            clans_data = [clan.get_state_info() for clan in self.clans]
            
            # Asegurarse de que la resource_grid sea la del Environment y se convierta a lista
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
                    'total_resources': self.environment.get_total_resources() # Añadir recursos
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