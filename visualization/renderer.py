# visualization/renderer.py - Renderizador mejorado con información territorial
import numpy as np

class SimulationRenderer:
    """Renderizador avanzado para convertir estados de simulación a formato frontend"""
    
    def __init__(self):
        self.last_rendered_time = 0
        self.territory_cache = {}
    
    def render_state(self, simulation_state):
        """Convierte estado de simulación a formato JSON enriquecido para frontend"""
        try:
            # Verificar que el estado tiene la estructura esperada
            if not simulation_state or 'clans' not in simulation_state:
                return self._get_emergency_state()
            
            rendered_state = {
                'time': simulation_state.get('time', 0),
                'step': simulation_state.get('step', 0),
                'resource_grid': self._prepare_resource_grid(simulation_state.get('resource_grid', [])),
                'clans': self._prepare_clans(simulation_state.get('clans', [])),
                'territorial_map': self._prepare_territorial_map(simulation_state),
                'emergent_patterns': simulation_state.get('emergent_patterns', []),
                'system_metrics': self._prepare_system_metrics(simulation_state),
                'interaction_data': self._prepare_interaction_data(simulation_state),
                'metadata': {
                    'renderer_version': '2.0',
                    'last_update': self.last_rendered_time,
                    'has_territorial_data': bool(simulation_state.get('territorial_boundaries')),
                    'has_patterns': bool(simulation_state.get('emergent_patterns'))
                }
            }
            
            self.last_rendered_time = simulation_state.get('time', 0)
            
            # Debug info
            print(f"Renderizado exitoso: {len(rendered_state['clans'])} clanes, "
                  f"patrones: {len(rendered_state['emergent_patterns'])}")
            
            return rendered_state
            
        except Exception as e:
            print(f"Error en renderizador: {e}")
            import traceback
            traceback.print_exc()
            return self._get_emergency_state()
    
    def _prepare_resource_grid(self, resource_grid):
        """Prepara la grilla de recursos con información adicional"""
        if not resource_grid:
            # Grid por defecto 50x50
            return [[np.random.uniform(30, 70) for _ in range(50)] for _ in range(50)]
        
        # Asegurar que es una lista de listas y normalizar valores
        if isinstance(resource_grid, np.ndarray):
            resource_grid = resource_grid.tolist()
        
        # Normalizar valores para mejor visualización
        processed_grid = []
        for row in resource_grid:
            processed_row = []
            for cell in row:
                # Asegurar que los valores estén en rango razonable
                normalized_value = max(0, min(100, float(cell)))
                processed_row.append(normalized_value)
            processed_grid.append(processed_row)
        
        return processed_grid
    
    def _prepare_clans(self, clans):
        """Prepara datos de clanes con información territorial y de estado"""
        prepared_clans = []
        
        for clan in clans:
            if clan.get('size', 0) <= 0:
                continue  # Saltar clanes extintos
            
            prepared_clan = {
                'id': clan.get('id', 0),
                'size': max(1, int(clan.get('size', 1))),
                'position': self._prepare_position(clan.get('position', [0, 0])),
                'state': clan.get('state', 'foraging'),
                'strategy': clan.get('strategy', 'cooperative'),
                'energy': max(0, min(100, float(clan.get('energy', 50)))),
                'morale': max(0, min(100, float(clan.get('morale', 50)))),
                'combat_strength': clan.get('combat_strength', 0),
                'territory_size': clan.get('territory_size', 0),
                'allies': clan.get('allies', []),
                'enemies': clan.get('enemies', []),
                
                # Información visual adicional
                'visual_size': self._calculate_visual_size(clan.get('size', 1)),
                'health_percentage': clan.get('energy', 50),
                'state_color': self._get_state_color(clan.get('state', 'foraging')),
                'strategy_symbol': self._get_strategy_symbol(clan.get('strategy', 'cooperative'))
            }
            
            prepared_clans.append(prepared_clan)
        
        print(f"Clanes preparados: {len(prepared_clans)}")
        for clan in prepared_clans:
            print(f"  Clan {clan['id']}: tamaño={clan['size']}, pos={clan['position']}, "
                  f"estado={clan['state']}, energía={clan['energy']:.1f}")
        
        return prepared_clans
    
    def _prepare_territorial_map(self, simulation_state):
        """Prepara mapa territorial para visualización"""
        territorial_boundaries = simulation_state.get('territorial_boundaries', {})
        
        territorial_data = {
            'boundaries': {},
            'disputed_areas': [],
            'control_density': {},
            'frontier_cells': []
        }
        
        for clan_id, boundary_info in territorial_boundaries.items():
            territorial_data['boundaries'][str(clan_id)] = {
                'territory_size': boundary_info.get('territory_size', 0),
                'perimeter_size': boundary_info.get('perimeter_size', 0),
                'compactness': boundary_info.get('compactness', 0),
                'center': boundary_info.get('center', [0, 0])
            }
        
        return territorial_data
    
    def _prepare_system_metrics(self, simulation_state):
        """Prepara métricas del sistema"""
        system_metrics = simulation_state.get('system_metrics', {})
        
        return {
            'total_population': system_metrics.get('total_population', 0),
            'active_clans': system_metrics.get('active_clans', 0),
            'total_territory': system_metrics.get('total_territory', 0),
            'total_interactions': system_metrics.get('total_interactions', 0),
            'system_stability': self._calculate_system_stability(simulation_state),
            'diversity_index': self._calculate_diversity_index(simulation_state.get('clans', [])),
            'territorial_fragmentation': self._calculate_territorial_fragmentation(simulation_state)
        }
    
    def _prepare_interaction_data(self, simulation_state):
        """Prepara datos de interacciones para visualización"""
        # Por ahora retorna estructura básica
        # Se puede expandir para mostrar redes de interacciones
        return {
            'total_interactions': simulation_state.get('system_metrics', {}).get('total_interactions', 0),
            'cooperation_rate': 0.5,  # Placeholder
            'conflict_rate': 0.3,     # Placeholder
            'alliance_networks': []   # Placeholder
        }
    
    def _prepare_position(self, position):
        """Asegura que la posición esté en formato correcto"""
        if isinstance(position, np.ndarray):
            position = position.tolist()
        
        if isinstance(position, list) and len(position) >= 2:
            return [float(position[0]), float(position[1])]
        
        return [0.0, 0.0]
    
    def _calculate_visual_size(self, clan_size):
        """Calcula tamaño visual apropiado para el clan"""
        # Tamaño visual basado en raíz cuadrada para mejor representación
        base_size = max(3, min(15, np.sqrt(clan_size) * 1.5))
        return float(base_size)
    
    def _get_state_color(self, state):
        """Retorna color asociado con el estado del clan"""
        state_colors = {
            'foraging': '#27ae60',      # Verde - buscando recursos
            'migrating': '#f39c12',     # Naranja - migrando
            'fighting': '#e74c3c',      # Rojo - en combate
            'resting': '#9b59b6'        # Púrpura - descansando
        }
        return state_colors.get(state, '#95a5a6')  # Gris por defecto
    
    def _get_strategy_symbol(self, strategy):
        """Retorna símbolo asociado con la estrategia del clan"""
        strategy_symbols = {
            'cooperative': '🤝',
            'aggressive': '⚔️',
            'defensive': '🛡️',
            'exploratory': '🔍'
        }
        return strategy_symbols.get(strategy, '❓')
    
    def _calculate_system_stability(self, simulation_state):
        """Calcula índice de estabilidad del sistema"""
        clans = simulation_state.get('clans', [])
        if not clans:
            return 0.0
        
        # Estabilidad basada en varianza de energías y tamaños
        energies = [clan.get('energy', 50) for clan in clans]
        sizes = [clan.get('size', 1) for clan in clans]
        
        energy_stability = 1.0 - (np.var(energies) / 2500)  # Normalizado
        size_stability = 1.0 - (np.var(sizes) / max(1, np.mean(sizes)**2))
        
        return max(0.0, min(1.0, (energy_stability + size_stability) / 2))
    
    def _calculate_diversity_index(self, clans):
        """Calcula índice de diversidad de estrategias"""
        if not clans:
            return 0.0
        
        # Contar estrategias diferentes
        strategies = [clan.get('strategy', 'cooperative') for clan in clans]
        unique_strategies = set(strategies)
        
        # Índice de Shannon simplificado
        total = len(strategies)
        diversity = 0.0
        
        for strategy in unique_strategies:
            proportion = strategies.count(strategy) / total
            if proportion > 0:
                diversity -= proportion * np.log(proportion)
        
        # Normalizar por máximo teórico (log(4) para 4 estrategias)
        max_diversity = np.log(4)
        return diversity / max_diversity if max_diversity > 0 else 0.0
    
    def _calculate_territorial_fragmentation(self, simulation_state):
        """Calcula fragmentación territorial del sistema"""
        territorial_boundaries = simulation_state.get('territorial_boundaries', {})
        
        if not territorial_boundaries:
            return 0.0
        
        # Fragmentación basada en compactness promedio
        compactness_values = [
            boundary.get('compactness', 0) 
            for boundary in territorial_boundaries.values()
        ]
        
        if not compactness_values:
            return 0.0
        
        avg_compactness = np.mean(compactness_values)
        # Invertir para que mayor fragmentación = menor compactness
        fragmentation = max(0.0, 1.0 - (avg_compactness / 10.0))  # Normalizar
        
        return min(1.0, fragmentation)
    
    def _get_emergency_state(self):
        """Retorna estado de emergencia cuando hay errores"""
        return {
            'time': 0,
            'step': 0,
            'resource_grid': [[50 for _ in range(50)] for _ in range(50)],
            'clans': [],
            'territorial_map': {
                'boundaries': {},
                'disputed_areas': [],
                'control_density': {},
                'frontier_cells': []
            },
            'emergent_patterns': [],
            'system_metrics': {
                'total_population': 0,
                'active_clans': 0,
                'total_territory': 0,
                'total_interactions': 0,
                'system_stability': 0.0,
                'diversity_index': 0.0,
                'territorial_fragmentation': 0.0
            },
            'interaction_data': {
                'total_interactions': 0,
                'cooperation_rate': 0.0,
                'conflict_rate': 0.0,
                'alliance_networks': []
            },
            'metadata': {
                'renderer_version': '2.0',
                'last_update': 0,
                'has_territorial_data': False,
                'has_patterns': False,
                'emergency_mode': True
            }
        }