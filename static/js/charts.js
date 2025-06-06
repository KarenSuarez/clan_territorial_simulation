// charts.js - Funcionalidad de gráficos para análisis
document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando sistema de gráficos...');
    
    // Variables globales para gráficos
    let populationChartInstance = null; // ¡Ahora global dentro de este ámbito!
    let resourceChartInstance = null; // Mantener por si se usa
    let spatialChartInstance = null;
    let distributionChartInstance = null; // Nuevo: para el gráfico de distribución

    // Configuración de colores
    const chartColors = {
        primary: '#3498db',
        secondary: '#2ecc71',
        accent: '#e74c3c',
        warning: '#f39c12',
        info: '#9b59b6'
    };
    
    // Inicializar gráficos si Chart.js está disponible
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
    
    function initializeCharts() {
        console.log('Configurando gráficos...');
        
        // Configuración por defecto para todos los gráficos
        Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
        Chart.defaults.font.size = 12;
        Chart.defaults.color = '#2c3e50';
        
        // Configurar gráfico de población si existe
        const populationCanvas = document.getElementById('populationChart');
        if (populationCanvas) {
            setupPopulationChart(populationCanvas);
        }
        
        // Configurar otros gráficos (los que están en otras páginas de análisis)
        setupAnalysisCharts();
    }
    
    function setupPopulationChart(canvas) {
        // Si ya existe una instancia, la destruimos antes de crear una nueva
        // Esto es crucial para evitar el "trabado" y que se alargue el gráfico
        if (populationChartInstance) {
            populationChartInstance.destroy();
        }

        const ctx = canvas.getContext('2d');
        
        populationChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Población Total',
                    data: [],
                    borderColor: chartColors.primary,
                    backgroundColor: chartColors.primary + '20',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Recursos Totales',
                    data: [],
                    borderColor: chartColors.secondary,
                    backgroundColor: chartColors.secondary + '20',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 0 // Desactivar animaciones para mejor rendimiento en tiempo real
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Pasos de Simulación'
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Población'
                        },
                        beginAtZero: true
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Recursos'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                        beginAtZero: true
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Evolución Temporal de la Simulación'
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            title: function(context) {
                                return 'Paso: ' + context[0].label;
                            },
                            label: function(context) {
                                return context.dataset.label + ': ' + context.parsed.y.toFixed(2);
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
        console.log('Gráfico de población configurado');
    }
    
    function setupAnalysisCharts() {
        // Configurar gráficos de análisis si existen
        setupConvergenceChart();
        setupSpatialChart();
        setupDistributionChart();
    }
    
    function setupConvergenceChart() {
        const canvas = document.getElementById('convergenceChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        // También destruir si ya existe para evitar duplicados
        if (canvas.chart) canvas.chart.destroy(); 
        
        canvas.chart = new Chart(ctx, { /* ... */ });
    }
    
    function setupSpatialChart() {
        const canvas = document.getElementById('spatialChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        if (canvas.chart) canvas.chart.destroy(); 

        spatialChartInstance = new Chart(ctx, { /* ... */ });
    }
    
    function setupDistributionChart() {
        const canvas = document.getElementById('distributionChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        if (canvas.chart) canvas.chart.destroy(); 

        distributionChartInstance = new Chart(ctx, { /* ... */ });
    }
    
    // Funciones para actualizar gráficos
    function updatePopulationChart(populationData, resourceData, labels) {
        if (!populationChartInstance) {
            console.warn('⚠️ populationChartInstance no está inicializado.');
            // Reintentar inicializar si no está listo
            const populationCanvas = document.getElementById('populationChart');
            if (populationCanvas) {
                setupPopulationChart(populationCanvas);
            } else {
                return; // No se puede renderizar sin canvas
            }
        }
        
        populationChartInstance.data.labels = labels;
        populationChartInstance.data.datasets[0].data = populationData;
        populationChartInstance.data.datasets[1].data = resourceData;
        
        // Limitar los puntos de datos para evitar que se "alargue"
        const maxDataPoints = 200; // Mantiene los últimos 200 pasos
        if (labels.length > maxDataPoints) {
            const startIndex = labels.length - maxDataPoints;
            populationChartInstance.data.labels = labels.slice(startIndex);
            populationChartInstance.data.datasets[0].data = populationData.slice(startIndex);
            populationChartInstance.data.datasets[1].data = resourceData.slice(startIndex);
        }

        populationChartInstance.update('none'); // Usar 'none' para evitar animaciones y mejorar rendimiento
    }
    
    function updateSpatialChart(controlledArea, freeArea, disputedArea) {
        if (!spatialChartInstance) return;
        
        spatialChartInstance.data.datasets[0].data = [controlledArea, freeArea, disputedArea];
        spatialChartInstance.update();
    }
    
    function addDataPoint(chartInstance, label, data) {
        if (!chartInstance) return;
        
        chartInstance.data.labels.push(label);
        chartInstance.data.datasets.forEach((dataset, index) => {
            dataset.data.push(data[index] || 0);
        });
        
        // Mantener solo los últimos 50 puntos para rendimiento
        if (chartInstance.data.labels.length > 50) {
            chartInstance.data.labels.shift();
            chartInstance.data.datasets.forEach(dataset => {
                dataset.data.shift();
            });
        }
        
        chartInstance.update('none');
    }
    
    function clearChart(chartInstance) {
        if (!chartInstance) return;
        
        chartInstance.data.labels = [];
        chartInstance.data.datasets.forEach(dataset => {
            dataset.data = [];
        });
        chartInstance.update();
    }
    
    // Funciones de utilidad para análisis
    function calculateMovingAverage(data, windowSize = 5) {
        const result = [];
        for (let i = 0; i < data.length; i++) {
            const start = Math.max(0, i - windowSize + 1);
            const subset = data.slice(start, i + 1);
            const average = subset.reduce((sum, val) => sum + val, 0) / subset.length;
            result.push(average);
        }
        return result;
    }
    
    function calculateTrend(data) {
        if (data.length < 2) return 'insufficient_data';
        
        const n = data.length;
        const sumX = (n * (n - 1)) / 2;
        const sumY = data.reduce((sum, val) => sum + val, 0);
        const sumXY = data.reduce((sum, val, index) => sum + (index * val), 0);
        const sumX2 = (n * (n - 1) * (2 * n - 1)) / 6;
        
        const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
        
        if (slope > 0.1) return 'increasing';
        if (slope < -0.1) return 'decreasing';
        return 'stable';
    }
    
    function generateTrendAnalysis(populationHistory, resourceHistory) {
        const analysis = {
            population: {
                trend: calculateTrend(populationHistory),
                average: populationHistory.reduce((sum, val) => sum + val, 0) / populationHistory.length,
                max: Math.max(...populationHistory),
                min: Math.min(...populationHistory),
                variance: 0
            },
            resources: {
                trend: calculateTrend(resourceHistory),
                average: resourceHistory.reduce((sum, val) => sum + val, 0) / resourceHistory.length,
                max: Math.max(...resourceHistory),
                min: Math.min(...resourceHistory),
                variance: 0
            }
        };
        
        // Calcular varianza
        analysis.population.variance = populationHistory.reduce((sum, val) => 
            sum + Math.pow(val - analysis.population.average, 2), 0) / populationHistory.length;
        
        analysis.resources.variance = resourceHistory.reduce((sum, val) => 
            sum + Math.pow(val - analysis.resources.average, 2), 0) / resourceHistory.length;
        
        return analysis;
    }
    
    // Exportar funciones para uso externo
    window.ChartController = {
        updatePopulationChart,
        updateSpatialChart,
        // addDataPoint, // Ya no es necesario si updatePopulationChart maneja todo
        clearChart,
        calculateMovingAverage,
        calculateTrend,
        generateTrendAnalysis,
        getPopulationChart: () => populationChartInstance,
        getSpatialChart: () => spatialChartInstance
    };
    
    
    // Funciones específicas para la página de análisis
    if (window.location.pathname.includes('analysis')) {
        setupAnalysisPage();
    }
    
    function setupAnalysisPage() {
        console.log('Configurando página de análisis...');
        
        // Configurar controles interactivos
        setupAnalysisControls();
        
        // Actualizar gráficos cada cierto tiempo si hay datos
        setInterval(updateAnalysisCharts, 5000);
    }
    
    function setupAnalysisControls() {
        // Control de rango de análisis
        const rangeControl = document.getElementById('analysisRange');
        if (rangeControl) {
            rangeControl.addEventListener('change', function() {
                updateAnalysisRange(this.value);
            });
        }
        
        // Control de tipo de gráfico
        const chartTypeControl = document.getElementById('chartType');
        if (chartTypeControl) {
            chartTypeControl.addEventListener('change', function() {
                updateChartType(this.value);
            });
        }
    }
    
    function updateAnalysisRange(range) {
        console.log('Actualizando rango de análisis:', range);
        // Implementar lógica para actualizar el rango de datos mostrados
    }
    
    function updateChartType(type) {
        console.log('Cambiando tipo de gráfico:', type);
        // Implementar lógica para cambiar el tipo de visualización
    }
    
    function updateAnalysisCharts() {
        // Actualizar gráficos de análisis con datos más recientes
        if (window.SimulationController) {
            const history = window.SimulationController.getHistory();
            if (history && history.population && history.population.length > 0) {
                const analysis = generateTrendAnalysis(
                    history.population.map(p => p.value),
                    history.resources.map(r => r.value)
                );
                
                updateAnalysisMetrics(analysis);
            }
        }
    }
    
    function updateAnalysisMetrics(analysis) {
        // Actualizar métricas en la interfaz
        const elements = {
            avgPopulation: document.getElementById('avgPopulation'),
            maxPopulation: document.getElementById('maxPopulation'),
            populationTrend: document.getElementById('populationTrend'),
            resourceStability: document.getElementById('resourceStability')
        };
        
        if (elements.avgPopulation) {
            elements.avgPopulation.textContent = analysis.population.average.toFixed(0);
        }
        
        if (elements.maxPopulation) {
            elements.maxPopulation.textContent = analysis.population.max.toFixed(0);
        }
        
        if (elements.populationTrend) {
            elements.populationTrend.textContent = analysis.population.trend;
        }
        
        if (elements.resourceStability) {
            const stability = analysis.resources.variance < 100 ? 'Alta' : 'Baja';
            elements.resourceStability.textContent = stability;
        }
    }
    
    console.log('Sistema de gráficos inicializado');
});