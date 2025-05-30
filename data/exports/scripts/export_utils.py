# clan_territorial_simulation/data/exports/scripts/export_utils.py
import json
import csv
from datetime import datetime

def export_simulation_data_csv(history, filepath="data/exports/simulation_data.csv"):
    if not history:
        return False
    with open(filepath, 'w', newline='') as csvfile:
        fieldnames = ['time', 'clan_id', 'clan_size', 'clan_position_x', 'clan_position_y', 'resource_grid']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for state in history:
            time = state['time']
            resource_grid_str = json.dumps(state['resource_grid'])
            for clan in state['clans']:
                writer.writerow({
                    'time': time,
                    'clan_id': clan['id'],
                    'clan_size': clan['size'],
                    'clan_position_x': clan['position'][0],
                    'clan_position_y': clan['position'][1],
                    'resource_grid': resource_grid_str
                })
    return True

def export_simulation_data_json(history, filepath="data/exports/simulation_data.json"):
    if not history:
        return False
    with open(filepath, 'w') as jsonfile:
        json.dump(history, jsonfile, indent=4)
    return True

def generate_scientific_report_html(history, current_mode, config_name, filepath="data/exports/report.html"):
    from flask import render_template_string
    from visualization.charts import plot_population_over_time, plot_territory_heatmap, analyze_spatial_patterns, visualize_convergence_metrics
    from analysis.statistics import calculate_clan_statistics, analyze_variable_correlation, analyze_probability_distributions

    if not history:
        return False

    population_chart = plot_population_over_time(history)
    territory_heatmap = plot_territory_heatmap(history, last_n_steps=100)
    spatial_patterns = analyze_spatial_patterns(history)
    # Assuming convergence analysis was run and results are stored (replace with actual loading)
    convergence_results = {}
    convergence_plot = visualize_convergence_metrics(convergence_results)
    clan_statistics = calculate_clan_statistics(history)
    variable_correlation = analyze_variable_correlation(history)
    population_distribution = analyze_probability_distributions(history)
    last_100_steps_data = json.dumps(history[-100:], indent=4) if len(history) > 100 else json.dumps(history, indent=4)
    report_generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    simulation_duration = len(history)

    template = open("data/exports/templates/report_template.html").read()
    rendered_report = render_template_string(template,
                                             simulation_mode=current_mode,
                                             config_name=config_name,
                                             simulation_duration=simulation_duration,
                                             population_chart=population_chart,
                                             territory_heatmap=territory_heatmap,
                                             spatial_patterns=spatial_patterns,
                                             convergence_plot=convergence_plot,
                                             clan_statistics=clan_statistics,
                                             variable_correlation=variable_correlation,
                                             population_distribution=population_distribution,
                                             last_100_steps_data=last_100_steps_data,
                                             report_generation_time=report_generation_time)

    with open(filepath, 'w') as f:
        f.write(rendered_report)
    return True

def generate_animation_html(history, filepath="data/exports/animation.html"):
    from flask import render_template_string
    if not history:
        return False
    animation_frames = json.dumps(history)
    template = open("data/exports/templates/animation_template.html").read()
    rendered_animation = render_template_string(template, animation_frames=animation_frames)
    with open(filepath, 'w') as f:
        f.write(rendered_animation)
    return True