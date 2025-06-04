import numpy as np

class Territory:
    """Representa el territorio controlado por un clan"""
    
    def __init__(self):
        self.area = 0
        self.controlled_cells = set()
        self.boundary_strength = 1.0
    
    def add_cell(self, position):
        """Añade una celda al territorio"""
        self.controlled_cells.add(tuple(position))
        self.area = len(self.controlled_cells)
    
    def remove_cell(self, position):
        """Remueve una celda del territorio"""
        self.controlled_cells.discard(tuple(position))
        self.area = len(self.controlled_cells)
    
    def contains(self, position):
        """Verifica si una posición está en el territorio"""
        return tuple(position) in self.controlled_cells
    
    def get_perimeter(self):
        """Calcula el perímetro del territorio"""
        if not self.controlled_cells:
            return 0
        
        perimeter = 0
        for cell in self.controlled_cells:
            x, y = cell
            # Contar celdas adyacentes que no están en el territorio
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                if (x+dx, y+dy) not in self.controlled_cells:
                    perimeter += 1
        
        return perimeter
    
    def get_centroid(self):
        """Calcula el centroide del territorio"""
        if not self.controlled_cells:
            return np.array([0, 0])
        
        x_coords = [cell[0] for cell in self.controlled_cells]
        y_coords = [cell[1] for cell in self.controlled_cells]
        
        return np.array([np.mean(x_coords), np.mean(y_coords)])