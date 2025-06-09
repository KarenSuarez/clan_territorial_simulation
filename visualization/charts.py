import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter

def plot_population_over_time(history):
    """Genera un gráfico de la población de cada clan a lo largo del tiempo."""
    if not history:
        return None

    fig = go.Figure()
    time_points = range(len(history))
    clan_ids = set()
    for state in history:
        for clan in state['clans']:
            clan_ids.add(clan['id'])

    for clan_id in sorted(list(clan_ids)):
        population_history = [state['clans'][c_idx]['size']
                              for state in history
                              for c_idx, clan in enumerate(state['clans']) if clan['id'] == clan_id]
        fig.add_trace(go.Scatter(x=time_points, y=population_history, mode='lines', name=f'Clan {clan_id}'))

    fig.update_layout(title='Población de Clanes a lo Largo del Tiempo',
                      xaxis_title='Tiempo (Pasos de Simulación)',
                      yaxis_title='Población')
    return fig.to_html(full_html=False)

def plot_territory_heatmap(history, last_n_steps=-1, blur_radius=2):
    """Genera un mapa de calor de la densidad territorial de los clanes."""
    if not history:
        return None

    if last_n_steps > 0:
        relevant_history = history[-last_n_steps:]
    else:
        relevant_history = history

    grid_size = relevant_history[0]['resource_grid'].shape if relevant_history else None
    if not grid_size:
        return None

    clan_presence = np.zeros(grid_size, dtype=float)
    for state in relevant_history:
        clan_territories = {}
        for clan in state['clans']:
            pos_x, pos_y = int(clan['position'][0]), int(clan['position'][1])
            if 0 <= pos_x < grid_size[0] and 0 <= pos_y < grid_size[1]:
                clan_presence[pos_y, pos_x] += 1

    blurred_presence = gaussian_filter(clan_presence, sigma=blur_radius)

    fig = go.Figure(data=go.Heatmap(z=blurred_presence,
                                   colorscale='Viridis',
                                   colorbar_title='Densidad Territorial'))
    fig.update_layout(title='Mapa de Calor de Densidad Territorial (Últimos {} Pasos)'.format(len(relevant_history)),
                      xaxis_title='X',
                      yaxis_title='Y',
                      yaxis_autorange='reversed',
                      xaxis_autorange=False,
                      yaxis_scaleanchor="x", yaxis_scaleratio=1)
    return fig.to_html(full_html=False)

def analyze_spatial_patterns(history):
    """Analiza patrones espaciales emergentes (ej: clustering)."""
    if not history:
        return "No hay datos para análisis espacial."

    final_state = history[-1]
    clan_positions = np.array([clan['position'] for clan in final_state['clans']])

    if len(clan_positions) < 2:
        return "Se necesitan al menos dos clanes para analizar patrones espaciales."

    from scipy.spatial.distance import pdist, squareform
    distances = pdist(clan_positions)
    avg_distance = np.mean(distances)

    return f"Análisis de Patrones Espaciales:\nDistancia promedio entre clanes: {avg_distance:.2f}"

def visualize_convergence_metrics(convergence_results):
    """Visualiza las métricas del análisis de convergencia."""
    if not convergence_results or not convergence_results.get('convergence_norms'):
        return "No hay resultados de convergencia para visualizar."

    fig = go.Figure()
    for key, value in convergence_results['convergence_norms'].items():
        dt_coarse, dt_fine = key.split('L2(')[1].split(')')[0].split(', ')
        fig.add_trace(go.Scatter(x=[float(dt_coarse)], y=[value], mode='markers+lines', name=key))

    fig.update_layout(title='Norma L2 de Convergencia vs. Paso de Tiempo (dt)',
                      xaxis_title='Paso de Tiempo (dt)',
                      yaxis_title='Norma L2',
                      yaxis_type="log")
    return fig.to_html(full_html=False)