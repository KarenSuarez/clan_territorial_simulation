import pandas as pd
import numpy as np
from scipy import stats

def calculate_clan_statistics(history):
    """Calcula estadísticas descriptivas por clan (tamaño promedio, máximo, mínimo)."""
    if not history:
        return "No hay datos para estadísticas de clanes."

    clan_data = {}
    clan_ids = set()
    for state in history:
        for clan in state['clans']:
            clan_ids.add(clan['id'])

    for clan_id in sorted(list(clan_ids)):
        sizes = [state['clans'][c_idx]['size']
                 for state in history
                 for c_idx, clan in enumerate(state['clans']) if clan['id'] == clan_id]
        if sizes:
            clan_data[f'Clan {clan_id}'] = {
                'mean_size': np.mean(sizes),
                'max_size': np.max(sizes),
                'min_size': np.min(sizes),
                'std_dev_size': np.std(sizes)
            }
    return pd.DataFrame.from_dict(clan_data, orient='index').to_html()

def analyze_variable_correlation(history):
    """Analiza la correlación entre diferentes variables (ej: tamaño del clan y recursos locales)."""
    if not history:
        return "No hay datos para análisis de correlación."

    data = []
    for state in history:
        for clan in state['clans']:
            local_resource = state['resource_grid'][int(clan['position'][1]), int(clan['position'][0])]
            data.append({'clan_size': clan['size'], 'local_resource': local_resource})

    df = pd.DataFrame(data)
    correlation_matrix = df.corr(method='pearson').to_html()
    return f"<h2>Matriz de Correlación entre Variables</h2>{correlation_matrix}"

def perform_significance_tests(history):
    """Realiza tests de significancia estadística (ej: diferencia de medias de tamaño entre clanes)."""
    if not history:
        return "No hay datos para tests de significancia."

    clan_sizes = {}
    for state in history:
        for clan in state['clans']:
            if clan['id'] not in clan_sizes:
                clan_sizes[clan['id']] = []
            clan_sizes[clan['id']].append(clan['size'])

    if len(clan_sizes) < 2:
        return "Se necesitan al menos dos clanes para realizar tests de significancia."

    results = "<h2>Tests de Significancia Estadística (Tamaño Promedio de Clanes)</h2>"
    clan_ids = list(clan_sizes.keys())
    for i in range(len(clan_ids)):
        for j in range(i + 1, len(clan_ids)):
            clan1_id = clan_ids[i]
            clan2_id = clan_ids[j]
            t_stat, p_value = stats.ttest_ind(clan_sizes[clan1_id], clan_sizes[clan2_id], equal_var=False)
            results += f"<p>Comparación Clan {clan1_id} vs Clan {clan2_id}: t-estadístico = {t_stat:.2f}, p-valor = {p_value:.3f}</p>"

    return results

def analyze_probability_distributions(history):
    """Analiza las distribuciones de probabilidad de variables clave (ej: tamaño de la población)."""
    if not history:
        return "No hay datos para análisis de distribuciones."

    population_sizes = [clan['size'] for state in history for clan in state['clans']]
    if not population_sizes:
        return "No hay datos de población para analizar distribuciones."

    import plotly.figure_factory as ff
    hist_data = [population_sizes]
    group_labels = ['Tamaño de la Población']
    fig = ff.create_distplot(hist_data, group_labels, bin_size=1, curve_type='kde')
    fig.update_layout(title='Distribución de Probabilidad del Tamaño de la Población',
                      xaxis_title='Tamaño de la Población',
                      yaxis_title='Densidad de Probabilidad')
    return fig.to_html(full_html=False)