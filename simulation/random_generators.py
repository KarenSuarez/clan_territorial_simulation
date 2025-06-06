# simulation/random_generators.py

import numpy as np

class MersenneTwister:
    def __init__(self, seed):
        # Usamos np.random.RandomState para aprovechar su implementación de Mersenne Twister
        # Esto es mucho más robusto que una implementación manual para fines de simulación compleja.
        self.rng = np.random.RandomState(seed)
        self.seed = seed  # Guardar la semilla para referencia

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

    def random_exponential(self, scale=1.0, size=None):
        """Genera números aleatorios de una distribución exponencial."""
        return self.rng.exponential(scale, size=size)

    def random_poisson(self, lam=1.0, size=None):
        """Genera números aleatorios de una distribución de Poisson."""
        return self.rng.poisson(lam, size=size)

    def random_beta(self, a, b, size=None):
        """Genera números aleatorios de una distribución beta."""
        return self.rng.beta(a, b, size=size)

    def random_gamma(self, shape, scale=1.0, size=None):
        """Genera números aleatorios de una distribución gamma."""
        return self.rng.gamma(shape, scale, size=size)

    def shuffle(self, array):
        """Mezcla una matriz en su lugar."""
        self.rng.shuffle(array)
        return array

    def permutation(self, x):
        """Retorna una permutación aleatoria de una secuencia."""
        return self.rng.permutation(x)

    def sample(self, population, k):
        """Retorna una muestra aleatoria de k elementos de la población."""
        if hasattr(population, '__len__'):
            indices = self.rng.choice(len(population), size=k, replace=False)
            return [population[i] for i in indices]
        else:
            # Si population es un iterable sin len(), convertir a lista
            pop_list = list(population)
            indices = self.rng.choice(len(pop_list), size=k, replace=False)
            return [pop_list[i] for i in indices]

    def weighted_choice(self, choices, weights):
        """Hace una elección aleatoria ponderada."""
        weights = np.array(weights)
        weights = weights / np.sum(weights)  # Normalizar
        return self.rng.choice(choices, p=weights)

    def random_walk(self, steps, step_size=1.0, dimensions=2):
        """Genera una caminata aleatoria."""
        if dimensions == 1:
            directions = self.rng.choice([-1, 1], size=steps)
            positions = np.cumsum(directions * step_size)
        elif dimensions == 2:
            angles = self.rng.uniform(0, 2*np.pi, size=steps)
            dx = np.cos(angles) * step_size
            dy = np.sin(angles) * step_size
            positions = np.cumsum(np.column_stack([dx, dy]), axis=0)
        else:
            # Para más dimensiones, generar direcciones aleatorias normalizadas
            directions = self.rng.normal(0, 1, size=(steps, dimensions))
            # Normalizar cada dirección
            norms = np.linalg.norm(directions, axis=1, keepdims=True)
            directions = directions / norms * step_size
            positions = np.cumsum(directions, axis=0)
        
        return positions

    def reset_seed(self, new_seed):
        """Reinicia el generador con una nueva semilla."""
        self.seed = new_seed
        self.rng = np.random.RandomState(new_seed)

    def get_state(self):
        """Obtiene el estado actual del generador."""
        return self.rng.get_state()

    def set_state(self, state):
        """Establece el estado del generador."""
        self.rng.set_state(state)

class LinearCongruentialGenerator:
    """Implementación simple de un generador congruencial lineal para casos específicos."""
    
    def __init__(self, seed, a=1664525, c=1013904223, m=2**32):
        self.seed = seed
        self.current = seed
        self.a = a  # Multiplicador
        self.c = c  # Incremento
        self.m = m  # Módulo

    def random_int(self):
        """Genera el siguiente entero aleatorio."""
        self.current = (self.a * self.current + self.c) % self.m
        return self.current

    def random_float(self):
        """Genera un flotante aleatorio entre 0.0 y 1.0."""
        return self.random_int() / self.m

    def random_uniform(self, low=0.0, high=1.0):
        """Genera un número aleatorio uniforme en el rango [low, high)."""
        return low + (high - low) * self.random_float()

    def random_randint(self, low, high):
        """Genera un entero aleatorio en el rango [low, high)."""
        range_size = high - low
        return low + (self.random_int() % range_size)

    def reset_seed(self, new_seed):
        """Reinicia el generador con una nueva semilla."""
        self.seed = new_seed
        self.current = new_seed

class XORShiftGenerator:
    """Implementación de XORShift para generación rápida de números aleatorios."""
    
    def __init__(self, seed):
        self.seed = seed
        self.state = seed if seed != 0 else 1  # XORShift no puede empezar con 0

    def random_int(self):
        """Genera el siguiente entero aleatorio usando XORShift."""
        self.state ^= self.state << 13
        self.state ^= self.state >> 17
        self.state ^= self.state << 5
        return self.state & 0xFFFFFFFF  # Mantener en 32 bits

    def random_float(self):
        """Genera un flotante aleatorio entre 0.0 y 1.0."""
        return self.random_int() / (2**32)

    def random_uniform(self, low=0.0, high=1.0):
        """Genera un número aleatorio uniforme en el rango [low, high)."""
        return low + (high - low) * self.random_float()

    def reset_seed(self, new_seed):
        """Reinicia el generador con una nueva semilla."""
        self.seed = new_seed
        self.state = new_seed if new_seed != 0 else 1

# Función de utilidad para crear generadores según el tipo
def create_generator(generator_type='mersenne', seed=None):
    """Factory function para crear diferentes tipos de generadores."""
    if seed is None:
        import time
        seed = int(time.time() * 1000000) % (2**32)
    
    if generator_type.lower() == 'mersenne':
        return MersenneTwister(seed)
    elif generator_type.lower() == 'lcg':
        return LinearCongruentialGenerator(seed)
    elif generator_type.lower() == 'xorshift':
        return XORShiftGenerator(seed)
    else:
        raise ValueError(f"Tipo de generador no soportado: {generator_type}")

# Ejemplo de uso y test unitario básico
if __name__ == '__main__':
    print("Probando generadores de números aleatorios...")
    
    # Test Mersenne Twister
    rng_mt = MersenneTwister(12345)
    print("\nMersenne Twister:")
    print("Random float:", rng_mt.random_float())
    print("Random uniform (0, 10):", rng_mt.random_uniform(0, 10))
    print("Random normal:", rng_mt.random_normal())
    print("Random randint (1, 10):", rng_mt.random_randint(1, 10))
    print("Random choice:", rng_mt.random_choice(['a', 'b', 'c', 'd'], size=3))
    
    # Test Linear Congruential Generator
    rng_lcg = LinearCongruentialGenerator(12345)
    print("\nLinear Congruential Generator:")
    print("Random float:", rng_lcg.random_float())
    print("Random uniform (0, 10):", rng_lcg.random_uniform(0, 10))
    print("Random randint (1, 10):", rng_lcg.random_randint(1, 10))
    
    # Test XORShift
    rng_xor = XORShiftGenerator(12345)
    print("\nXORShift Generator:")
    print("Random float:", rng_xor.random_float())
    print("Random uniform (0, 10):", rng_xor.random_uniform(0, 10))
    
    # Test Factory Function
    print("\nUsando factory function:")
    rng_factory = create_generator('mersenne', 54321)
    print("Random walk 2D (5 pasos):")
    walk = rng_factory.random_walk(5, step_size=1.0, dimensions=2)
    print(walk)
    
    print("\nTodos los tests completados exitosamente!")