# clan_territorial_simulation/utils/performance.py
import numpy as np
import functools
import threading

def vectorized_clan_movement(clans, environment, dt):
    """Vectorización del movimiento de todos los clanes."""
    if not clans:
        return

    positions = np.array([clan.position for clan in clans])
    velocities = np.array([clan.velocity for clan in clans])
    gradients = np.array([environment.get_resource_gradient(pos) for pos in positions])
    sigmas = np.array([clan.sigma for clan in clans])
    epsilons = np.random.normal(0, 1, size=positions.shape) # Generar ruido vectorizado

    delta_positions = velocities * gradients + sigmas[:, np.newaxis] * epsilons
    new_positions = positions + delta_positions * dt

    for i, clan in enumerate(clans):
        clan.move(environment.get_toroidal_position(new_positions[i]))

def cache_method(maxsize=128):
    """Decorator para cachear los resultados de un método."""
    def decorator(func):
        @functools.lru_cache(maxsize=maxsize)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

def parallel_execution(func, args_list, num_threads=4):
    """Ejecuta una función en paralelo con diferentes argumentos."""
    threads = []
    results = [None] * len(args_list)

    def worker(index, args):
        results[index] = func(*args)

    for i, args in enumerate(args_list):
        thread = threading.Thread(target=worker, args=(i, args))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return results