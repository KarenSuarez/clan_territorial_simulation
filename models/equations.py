# clan_territorial_simulation/models/equations.py
import numpy as np
from config import RESOURCE_MAX, MORTALITY_STARVATION_MAX, RESOURCE_REQUIRED_PER_INDIVIDUAL

def population_dynamics(n, beta, mu, mu_c, mu_s):
    return (beta - mu - mu_c - mu_s) * n

def resource_evolution(r, alpha, consumption):
    return alpha * RESOURCE_MAX * (1 - r / RESOURCE_MAX) - consumption

def starvation_mortality(resource_available):
    if RESOURCE_REQUIRED_PER_INDIVIDUAL == 0:
        return 0.0
    return MORTALITY_STARVATION_MAX * np.exp(-resource_available / RESOURCE_REQUIRED_PER_INDIVIDUAL)

# clan_territorial_simulation/models/equations.py (continuación)
def cooperative_consumption(n_individuals, clan_size, lambda_param, local_resource_density, foraging_efficiency):
    return n_individuals * (clan_size**(1 - lambda_param)) * local_resource_density * foraging_efficiency

def clan_movement(velocity, gradient, sigma, epsilon):
    return velocity * gradient + sigma * epsilon