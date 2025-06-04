# models/environment.py
import numpy as np

class Environment:
    def __init__(self, grid_size=(50, 50)):
        self.grid_size = np.array(grid_size)
        self.grid = np.random.uniform(30, 80, grid_size)  # Recursos iniciales
        self.max_resource = 100.0
        self.regeneration_rate = 1.5
    
    def is_valid_position(self, position):
        """Verifica si una posición está dentro del grid"""
        return (0 <= position[0] < self.grid_size[0] and 
                0 <= position[1] < self.grid_size[1])
    
    def get_toroidal_position(self, position):
        """Convierte posición a coordenadas toroidales"""
        return np.mod(position, self.grid_size)
    
    def get_resource(self, position):
        """Obtiene la cantidad de recurso en una posición"""
        if len(position) == 2:
            pos = self.get_toroidal_position(np.array(position)).astype(int)
            return self.grid[pos[0], pos[1]]
        else:
            # Manejar caso donde position es un entero (coordenada x, y separada)
            x, y = position if hasattr(position, '__iter__') else (position, 0)
            pos = self.get_toroidal_position(np.array([x, y])).astype(int)
            return self.grid[pos[0], pos[1]]
    
    def consume(self, position, amount):
        """Consume recursos de una posición"""
        pos = self.get_toroidal_position(np.array(position)).astype(int)
        current = self.grid[pos[0], pos[1]]
        consumed = min(current, amount)
        self.grid[pos[0], pos[1]] = max(0, current - consumed)
        return consumed
    
    def consume_resource(self, position, amount):
        """Alias para consume - compatibilidad"""
        return self.consume(position, amount)
    
    def regenerate(self, dt):
        """Regenera recursos usando crecimiento logístico"""
        # Crecimiento logístico
        growth = self.regeneration_rate * self.grid * (1 - self.grid / self.max_resource) * dt
        self.grid = np.minimum(self.grid + growth, self.max_resource)
        
        # Añadir variabilidad estocástica pequeña
        noise = np.random.normal(0, 0.05, self.grid.shape) * dt
        self.grid = np.maximum(0, self.grid + noise)
    
    def get_resource_density(self):
        """Calcula la densidad promedio de recursos"""
        return np.mean(self.grid)
    
    def get_total_resources(self):
        """Obtiene el total de recursos en el entorno"""
        return np.sum(self.grid)
    
    def __repr__(self):
        return f"Environment(size={self.grid_size}, avg_resource={self.get_resource_density():.2f})"