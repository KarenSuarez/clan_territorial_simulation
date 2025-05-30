# clan_territorial_simulation/simulation/random_generators.py
import numpy as np

class MersenneTwister:
    def __init__(self, seed):
        self.state = np.array([seed] + [0] * 623, dtype=np.uint32)
        self.index = 0
        self.initialize(seed)

    def initialize(self, seed):
        self.state[0] = seed & 0xffffffff
        for i in range(1, 624):
            self.state[i] = (1812433253 * (self.state[i - 1] ^ (self.state[i - 1] >> 30)) + i) & 0xffffffff
        self.index = 0

    def twist(self):
        for i in range(624):
            y = (self.state[i] & 0x80000000) + (self.state[(i + 1) % 624] & 0x7fffffff)
            self.state[i] = self.state[(i + 397) % 624] ^ (y >> 1)
            if y % 2 != 0:
                self.state[i] ^= 0x9908b0df
        self.index = 0

    def random_uint32(self):
        if self.index == 0:
            self.twist()
        y = self.state[self.index]
        y ^= (y >> 11)
        y ^= (y << 7) & 0x9d2c5680
        y ^= (y << 15) & 0xefc60000
        y ^= (y >> 18)
        self.index = (self.index + 1) % 624
        return y

    def random_float(self):
        return self.random_uint32() / 4294967295.0

    def random_normal(self, mean=0.0, std_dev=1.0):
        # Box-Muller transform for normal distribution
        u1 = self.random_float()
        u2 = self.random_float()
        z0 = np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2)
        return mean + std_dev * z0

# Ejemplo de uso
if __name__ == '__main__':
    rng = MersenneTwister(12345)
    print("Random uint32:", rng.random_uint32())
    print("Random float:", rng.random_float())
    print("Random normal:", rng.random_normal())