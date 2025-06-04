import numpy as np

def population_dynamics(current_population, birth_rate, natural_death_rate, competition_rate, starvation_rate):
    """
    Ecuación diferencial para dinámicas poblacionales
    dN/dt = birth_rate * N - natural_death_rate * N - competition_rate * N - starvation_rate * N
    """
    if current_population <= 0:
        return 0
    
    growth = birth_rate * current_population
    deaths = (natural_death_rate + competition_rate + starvation_rate) * current_population
    
    return growth - deaths

def starvation_mortality(resource_per_capita, threshold=0.5, max_mortality=0.3):
    """
    Calcula la mortalidad por inanición basada en recursos per capita
    """
    if resource_per_capita >= threshold:
        return 0.0
    
    # Mortalidad exponencial cuando los recursos son escasos
    mortality = max_mortality * np.exp(-resource_per_capita / threshold)
    return min(mortality, max_mortality)

def cooperative_consumption(individual_consumption, group_size, cooperation_factor, 
                          resource_concentration, efficiency):
    """
    Modelo de consumo cooperativo de recursos
    """
    cooperation_bonus = cooperation_factor * np.log(1 + group_size)
    base_consumption = individual_consumption * efficiency
    
    return base_consumption * (1 + cooperation_bonus) * resource_concentration

def clan_movement(current_position, resource_gradient, movement_speed, noise_std=0.1):
    """
    Calcula el movimiento del clan basado en gradiente de recursos
    """
    # Movimiento dirigido hacia recursos
    movement = movement_speed * resource_gradient
    
    # Añadir ruido estocástico
    noise = np.random.normal(0, noise_std, size=movement.shape)
    
    return movement + noise