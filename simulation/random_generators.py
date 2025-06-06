# clan_territorial_simulation/simulation/random_generators.py

import numpy as np

class MersenneTwister:
    def __init__(self, seed):
        # Usamos np.random.RandomState para aprovechar su implementación de Mersenne Twister
        # Esto es mucho más robusto que una implementación manual para fines de simulación compleja.
        self.rng = np.random.RandomState(seed)
        self.seed = seed # Guardar la semilla para referencia

    def random_float(self):
        """Genera un flotante aleatorio entre 0.0 y 1.0."""
        return self.rng.rand()

    def random_uniform(self, low=0.0, high=1.0, size=None):
        """Genera números aleatorios de una distribución uniforme."""
        return self.rng.uniform(low, high, size=size)

    def random_normal(self, mean=0.0, std_dev=1.0, size=None):
        """Genera números aleatorios de una distribución normal (gaussiana)."""
        return self.rng.normal(mean, std_dev, size=size)
    
    def random_randint(self, low, high=None, size=None):
        """Genera enteros aleatorios."""
        return self.rng.randint(low, high, size=size)

    def random_choice(self, a, size=None, replace=True, p=None):
        """Genera una muestra aleatoria de una matriz dada."""
        return self.rng.choice(a, size=size, replace=replace, p=p)

# Ejemplo de uso (el if __name__ == '__main__': se puede dejar como está, solo para pruebas)
if __name__ == '__main__':
    rng_test = MersenneTwister(12345)
    print("Random float:", rng_test.random_float())
    print("Random uniform (5):", rng_test.random_uniform(0, 10, 5))
    print("Random normal:", rng_test.random_normal())
    print("Random randint (1, 10):", rng_test.random_randint(1, 10))