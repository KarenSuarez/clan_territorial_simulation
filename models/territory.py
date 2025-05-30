# clan_territorial_simulation/models/territory.py
import numpy as np

class Territory:
    def __init__(self, area=None):
        self.area = area if area is not None else [] # Representación del territorio (ej: lista de celdas)

    def update(self, new_area):
        self.area = new_area

    def overlaps_with(self, other_territory):
        """Verifica si hay superposición con otro territorio."""
        if self.area is None or other_territory.area is None:
            return False
        return any(cell in other_territory.area for cell in self.area)

    def calculate_size(self):
        """Calcula el tamaño del territorio."""
        return len(self.area) if self.area is not None else 0

    # Métodos adicionales para análisis territorial (centroide, límites, etc.)
    def get_centroid(self):
        if not self.area:
            return None
        coords = np.array(self.area)
        return np.mean(coords, axis=0)

    # ... otros métodos para manejo avanzado de territorios ...