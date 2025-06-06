# models/environment.py

import numpy as np

class Environment:
    def __init__(self, grid_size=(50, 50), max_resource=100.0, regeneration_rate=1.5):
        self.grid_size = np.array(grid_size)
        self.grid = np.zeros(grid_size)  # Inicialización real se hará desde app.py o desde el engine
        self.max_resource = max_resource
        self.regeneration_rate = regeneration_rate

        # El RNG ahora lo recibirá desde el modo o Engine. Por ahora, si no lo tiene, usa np.random
        self.rng = None

    def set_rng(self, rng_instance):
        """Permite que el RNG se inyecte en el entorno."""
        self.rng = rng_instance

    def is_valid_position(self, position):
        """Verifica si una posición está dentro del grid."""
        return (0 <= position[0] < self.grid_size[0] and
                0 <= position[1] < self.grid_size[1])

    def get_toroidal_position(self, position):
        """Convierte posición a coordenadas toroidales."""
        return np.mod(position, self.grid_size)

    def get_resource(self, position):
        """Obtiene la cantidad de recurso en una posición."""
        pos = self.get_toroidal_position(np.array(position)).astype(int)
        return self.grid[pos[0], pos[1]]

    def consume(self, position, amount):
        """Consume recursos de una posición."""
        pos = self.get_toroidal_position(np.array(position)).astype(int)
        current = self.grid[pos[0], pos[1]]
        consumed = min(current, amount)
        self.grid[pos[0], pos[1]] = max(0, current - consumed)
        return consumed

    def consume_resource(self, position, amount):
        """Alias para consume - compatibilidad."""
        return self.consume(position, amount)

    def regenerate(self, dt):
        """Regenera recursos usando crecimiento logístico."""
        # Crecimiento logístico
        growth = self.regeneration_rate * self.grid * (1 - self.grid / self.max_resource) * dt
        self.grid = np.minimum(self.grid + growth, self.max_resource)

        # Añadir variabilidad estocástica pequeña, usando self.rng si está disponible
        if self.rng:
            noise = self.rng.random_normal(0, 0.05, size=self.grid.shape) * dt
        else:
            noise = np.random.normal(0, 0.05, self.grid.shape) * dt  # Fallback si no hay RNG asignado
        self.grid = np.maximum(0, self.grid + noise)

    def get_resource_density(self):
        """Calcula la densidad promedio de recursos."""
        return np.mean(self.grid)

    def get_total_resources(self):
        """Obtiene el total de recursos en el entorno."""
        return np.sum(self.grid)

    def get_resource_grid_info(self):
        """Retorna información estadística del grid de recursos."""
        return {
            'total': self.get_total_resources(),
            'average': self.get_resource_density(),
            'max': np.max(self.grid),
            'min': np.min(self.grid),
            'std': np.std(self.grid),
            'grid_size': self.grid_size.tolist(),
            'max_capacity': self.max_resource * self.grid_size[0] * self.grid_size[1]
        }

    def get_resource_distribution(self):
        """Retorna la distribución de recursos para análisis."""
        flattened = self.grid.flatten()
        return {
            'histogram': np.histogram(flattened, bins=20),
            'percentiles': {
                'p25': np.percentile(flattened, 25),
                'p50': np.percentile(flattened, 50),
                'p75': np.percentile(flattened, 75),
                'p90': np.percentile(flattened, 90),
                'p95': np.percentile(flattened, 95)
            }
        }

    def get_local_resource_density(self, position, radius=2):
        """Obtiene la densidad promedio de recursos en un área local."""
        pos = self.get_toroidal_position(np.array(position)).astype(int)
        total_resources = 0
        cell_count = 0

        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx*dx + dy*dy <= radius*radius:  # Círculo en lugar de cuadrado
                    check_pos = self.get_toroidal_position(pos + np.array([dx, dy])).astype(int)
                    total_resources += self.grid[check_pos[0], check_pos[1]]
                    cell_count += 1

        return total_resources / cell_count if cell_count > 0 else 0

    def add_resource_patch(self, center_position, radius, amount):
        """Añade un parche de recursos en una ubicación específica."""
        center = self.get_toroidal_position(np.array(center_position)).astype(int)
        
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                distance = np.sqrt(dx*dx + dy*dy)
                if distance <= radius:
                    # Distribución gaussiana dentro del parche
                    intensity = np.exp(-(distance**2) / (2 * (radius/3)**2))
                    patch_pos = self.get_toroidal_position(center + np.array([dx, dy])).astype(int)
                    
                    added_resource = amount * intensity
                    current_resource = self.grid[patch_pos[0], patch_pos[1]]
                    self.grid[patch_pos[0], patch_pos[1]] = min(
                        self.max_resource, 
                        current_resource + added_resource
                    )

    def deplete_area(self, center_position, radius, depletion_factor=0.5):
        """Agota recursos en un área específica."""
        center = self.get_toroidal_position(np.array(center_position)).astype(int)
        
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                distance = np.sqrt(dx*dx + dy*dy)
                if distance <= radius:
                    # Deplección más intensa en el centro
                    intensity = 1.0 - (distance / radius) * 0.5  # Entre 0.5 y 1.0
                    depletion_pos = self.get_toroidal_position(center + np.array([dx, dy])).astype(int)
                    
                    current_resource = self.grid[depletion_pos[0], depletion_pos[1]]
                    depleted_amount = current_resource * depletion_factor * intensity
                    self.grid[depletion_pos[0], depletion_pos[1]] = max(0, current_resource - depleted_amount)

    def reset_resources(self, distribution_type='uniform', **kwargs):
        """Reinicia la distribución de recursos según el tipo especificado."""
        if distribution_type == 'uniform':
            value = kwargs.get('value', self.max_resource * 0.5)
            self.grid.fill(value)
        
        elif distribution_type == 'random_uniform':
            min_val = kwargs.get('min_val', self.max_resource * 0.3)
            max_val = kwargs.get('max_val', self.max_resource * 0.8)
            if self.rng:
                self.grid = self.rng.random_uniform(min_val, max_val, self.grid_size)
            else:
                self.grid = np.random.uniform(min_val, max_val, self.grid_size)
        
        elif distribution_type == 'gaussian':
            mean = kwargs.get('mean', self.max_resource * 0.5)
            std = kwargs.get('std', self.max_resource * 0.2)
            if self.rng:
                self.grid = np.clip(self.rng.random_normal(mean, std, self.grid_size), 0, self.max_resource)
            else:
                self.grid = np.clip(np.random.normal(mean, std, self.grid_size), 0, self.max_resource)
        
        elif distribution_type == 'patches':
            # Múltiples parches de recursos altos
            self.grid.fill(self.max_resource * 0.1)  # Fondo bajo
            num_patches = kwargs.get('num_patches', 5)
            patch_radius = kwargs.get('patch_radius', 5)
            patch_intensity = kwargs.get('patch_intensity', self.max_resource * 0.9)
            
            for _ in range(num_patches):
                if self.rng:
                    patch_center = [
                        self.rng.random_randint(0, self.grid_size[0]),
                        self.rng.random_randint(0, self.grid_size[1])
                    ]
                else:
                    patch_center = [
                        np.random.randint(0, self.grid_size[0]),
                        np.random.randint(0, self.grid_size[1])
                    ]
                self.add_resource_patch(patch_center, patch_radius, patch_intensity)

    def get_gradient(self, position):
        """Calcula el gradiente de recursos en una posición."""
        pos = self.get_toroidal_position(np.array(position)).astype(int)
        
        # Calcular gradiente usando diferencias finitas
        dx_pos = self.get_toroidal_position(pos + np.array([1, 0])).astype(int)
        dx_neg = self.get_toroidal_position(pos + np.array([-1, 0])).astype(int)
        dy_pos = self.get_toroidal_position(pos + np.array([0, 1])).astype(int)
        dy_neg = self.get_toroidal_position(pos + np.array([0, -1])).astype(int)
        
        grad_x = (self.grid[dx_pos[0], dx_pos[1]] - self.grid[dx_neg[0], dx_neg[1]]) / 2.0
        grad_y = (self.grid[dy_pos[0], dy_pos[1]] - self.grid[dy_neg[0], dy_neg[1]]) / 2.0
        
        return np.array([grad_x, grad_y])

    def find_resource_hotspots(self, threshold_percentile=90):
        """Encuentra las ubicaciones con más recursos (hotspots)."""
        threshold = np.percentile(self.grid, threshold_percentile)
        hotspots = []
        
        for i in range(self.grid_size[0]):
            for j in range(self.grid_size[1]):
                if self.grid[i, j] >= threshold:
                    hotspots.append({
                        'position': [i, j],
                        'resource_level': self.grid[i, j],
                        'relative_density': self.grid[i, j] / self.max_resource
                    })
        
        # Ordenar por nivel de recursos
        hotspots.sort(key=lambda x: x['resource_level'], reverse=True)
        return hotspots

    def __repr__(self):
        return f"Environment(size={self.grid_size}, avg_resource={self.get_resource_density():.2f}, total={self.get_total_resources():.1f})"