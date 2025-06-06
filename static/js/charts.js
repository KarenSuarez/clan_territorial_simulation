// charts.js - Funcionalidad de gráficos para análisis (CORREGIDO)
document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando sistema de gráficos...');
    
    // Variables globales para gráficos
    let populationChartInstance = null;
    let resourceChartInstance = null;
    let spatialChartInstance = null;
    let distributionChartInstance = null;

    // Datos para los gráficos
    let chartData = {
        labels: [],
        populationData: [],
        resourceData: [],
        maxDataPoints: 100  // LÍMITE MÁXIMO DE PUNTOS
    };

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
        console.log('✅ Chart.js disponible, inicializando gráficos');
    } else {
        console.warn('⚠️ Chart.js no está disponible');
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
        } else {
            console.warn('⚠️ Canvas populationChart no encontrado');
        }
        
        // Configurar otros gráficos
        setupAnalysisCharts();
    }
    
    function setupPopulationChart(canvas) {
        console.log('🔧 Configurando gráfico de población...');
        
        // Destruir instancia anterior si existe
        if (populationChartInstance) {
            populationChartInstance.destroy();
            populationChartInstance = null;
        }

        const ctx = canvas.getContext('2d');
        
        populationChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Población Total',
                    data: chartData.populationData,
                    borderColor: chartColors.primary,
                    backgroundColor: chartColors.primary + '20',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 2,
                    pointHoverRadius: 4
                }, {
                    label: 'Recursos Totales',
                    data: chartData.resourceData,
                    borderColor: chartColors.secondary,
                    backgroundColor: chartColors.secondary + '20',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 2,
                    pointHoverRadius: 4,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 0 // Sin animaciones para mejor rendimiento
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Evolución Temporal de la Simulación',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
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
                                let value = parseFloat(context.parsed.y).toFixed(1);
                                return context.dataset.label + ': ' + value;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Pasos de Simulación'
                        },
                        ticks: {
                            maxTicksLimit: 10 // Limitar número de etiquetas
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
                        beginAtZero: true,
                        grace: '5%'
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
                        beginAtZero: true,
                        grace: '5%'
                    }
                }
            }
        });
        
        console.log('✅ Gráfico de población configurado exitosamente');
    }
    
    function setupAnalysisCharts() {
        // Configurar otros gráficos si existen
        setupConvergenceChart();
        setupSpatialChart();
        setupDistributionChart();
    }
    
    function setupConvergenceChart() {
        const canvas = document.getElementById('convergenceChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        if (canvas.chart) canvas.chart.destroy(); 
        
        // Configuración básica para gráfico de convergencia
        canvas.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Varianza Poblacional',
                    data: [],
                    borderColor: chartColors.warning,
                    backgroundColor: chartColors.warning + '20'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Análisis de Convergencia'
                    }
                }
            }
        });
    }
    
    function setupSpatialChart() {
        const canvas = document.getElementById('spatialChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        if (canvas.chart) canvas.chart.destroy(); 

        spatialChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Área Controlada', 'Área Libre', 'Área Disputada'],
                datasets: [{
                    data: [0, 100, 0],
                    backgroundColor: [
                        chartColors.primary,
                        chartColors.secondary,
                        chartColors.accent
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Distribución Territorial'
                    }
                }
            }
        });
    }
    
    function setupDistributionChart() {
        const canvas = document.getElementById('distributionChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        if (canvas.chart) canvas.chart.destroy(); 

        distributionChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Distribución de Clanes por Tamaño',
                    data: [],
                    backgroundColor: chartColors.info + '80'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Distribución de Tamaños de Clanes'
                    }
                }
            }
        });
    }
    
    // FUNCIÓN PRINCIPAL PARA ACTUALIZAR GRÁFICO DE POBLACIÓN
    function updatePopulationChart(step, populationValue, resourceValue) {
        if (!populationChartInstance) {
            console.warn('⚠️ populationChartInstance no está inicializado.');
            // Reintentar inicializar
            const populationCanvas = document.getElementById('populationChart');
            if (populationCanvas) {
                setupPopulationChart(populationCanvas);
            } else {
                return;
            }
        }
        
        // Agregar nuevos datos
        chartData.labels.push(step);
        chartData.populationData.push(populationValue);
        chartData.resourceData.push(resourceValue);
        
        // IMPORTANTE: Limitar datos para evitar crecimiento infinito
        if (chartData.labels.length > chartData.maxDataPoints) {
            chartData.labels.shift();
            chartData.populationData.shift();
            chartData.resourceData.shift();
        }
        
        // Actualizar el gráfico
        populationChartInstance.data.labels = [...chartData.labels];
        populationChartInstance.data.datasets[0].data = [...chartData.populationData];
        populationChartInstance.data.datasets[1].data = [...chartData.resourceData];
        
        // Actualizar sin animación para mejor rendimiento
        populationChartInstance.update('none');
        
        // Debug log ocasional
        if (step % 20 === 0) {
            console.log(`📊 Gráfico actualizado: paso ${step}, puntos: ${chartData.labels.length}/${chartData.maxDataPoints}`);
        }
    }
    
    function updateSpatialChart(controlledArea, freeArea, disputedArea) {
        if (!spatialChartInstance) return;
        
        spatialChartInstance.data.datasets[0].data = [controlledArea, freeArea, disputedArea];
        spatialChartInstance.update('none');
    }
    
    function clearAllCharts() {
        console.log('🧹 Limpiando todos los gráficos...');
        
        // Limpiar datos
        chartData.labels = [];
        chartData.populationData = [];
        chartData.resourceData = [];
        
        // Actualizar gráfico de población
        if (populationChartInstance) {
            populationChartInstance.data.labels = [];
            populationChartInstance.data.datasets[0].data = [];
            populationChartInstance.data.datasets[1].data = [];
            populationChartInstance.update('none');
        }
        
        // Limpiar otros gráficos
        if (spatialChartInstance) {
            spatialChartInstance.data.datasets[0].data = [0, 100, 0];
            spatialChartInstance.update('none');
        }
        
        console.log('✅ Gráficos limpiados');
    }
    
    function resizeCharts() {
        console.log('📏 Redimensionando gráficos...');
        
        if (populationChartInstance) {
            populationChartInstance.resize();
        }
        if (spatialChartInstance) {
            spatialChartInstance.resize();
        }
        if (distributionChartInstance) {
            distributionChartInstance.resize();
        }
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
    
    function generateTrendAnalysis() {
        if (chartData.populationData.length < 5) {
            return { 
                status: 'insufficient_data',
                message: 'Necesitas al menos 5 puntos de datos para el análisis'
            };
        }
        
        const analysis = {
            population: {
                trend: calculateTrend(chartData.populationData),
                average: chartData.populationData.reduce((sum, val) => sum + val, 0) / chartData.populationData.length,
                max: Math.max(...chartData.populationData),
                min: Math.min(...chartData.populationData),
                current: chartData.populationData[chartData.populationData.length - 1]
            },
            resources: {
                trend: calculateTrend(chartData.resourceData),
                average: chartData.resourceData.reduce((sum, val) => sum + val, 0) / chartData.resourceData.length,
                max: Math.max(...chartData.resourceData),
                min: Math.min(...chartData.resourceData),
                current: chartData.resourceData[chartData.resourceData.length - 1]
            },
            correlation: calculateCorrelation(chartData.populationData, chartData.resourceData)
        };
        
        return analysis;
    }
    
    function calculateCorrelation(x, y) {
        if (x.length !== y.length || x.length < 2) return 0;
        
        const n = x.length;
        const sumX = x.reduce((sum, val) => sum + val, 0);
        const sumY = y.reduce((sum, val) => sum + val, 0);
        const sumXY = x.reduce((sum, val, i) => sum + (val * y[i]), 0);
        const sumX2 = x.reduce((sum, val) => sum + (val * val), 0);
        const sumY2 = y.reduce((sum, val) => sum + (val * val), 0);
        
        const correlation = (n * sumXY - sumX * sumY) / 
            Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));
        
        return isNaN(correlation) ? 0 : correlation;
    }
    
    // Redimensionar gráficos cuando cambie el tamaño de la ventana
    window.addEventListener('resize', () => {
        setTimeout(resizeCharts, 100);
    });
    
    // Exportar funciones para uso externo
    window.ChartController = {
        updatePopulationChart: updatePopulationChart,
        updateSpatialChart: updateSpatialChart,
        clearAllCharts: clearAllCharts,
        resizeCharts: resizeCharts,
        calculateMovingAverage: calculateMovingAverage,
        calculateTrend: calculateTrend,
        generateTrendAnalysis: generateTrendAnalysis,
        getPopulationChart: () => populationChartInstance,
        getSpatialChart: () => spatialChartInstance,
        getChartData: () => ({ ...chartData }), // Copia de los datos
        setMaxDataPoints: (max) => {
            chartData.maxDataPoints = Math.max(10, Math.min(500, max));
            console.log(`📊 Máximo de puntos establecido en: ${chartData.maxDataPoints}`);
        }
    };
    
    // Configuración específica para la página de análisis
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
        const newMaxPoints = parseInt(range) || 100;
        window.ChartController.setMaxDataPoints(newMaxPoints);
    }
    
    function updateChartType(type) {
        console.log('Cambiando tipo de gráfico:', type);
        // Implementar lógica para cambiar el tipo de visualización
    }
    
    function updateAnalysisCharts() {
        // Actualizar gráficos de análisis con datos más recientes
        if (window.SimulationController) {
            const state = window.SimulationController.getState();
            if (state && state.system_metrics) {
                // Actualizar con datos actuales si están disponibles
                const analysis = generateTrendAnalysis();
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
        
        if (analysis.status === 'insufficient_data') {
            Object.values(elements).forEach(el => {
                if (el) el.textContent = 'N/A';
            });
            return;
        }
        
        if (elements.avgPopulation) {
            elements.avgPopulation.textContent = analysis.population.average.toFixed(0);
        }
        
        if (elements.maxPopulation) {
            elements.maxPopulation.textContent = analysis.population.max.toFixed(0);
        }
        
        if (elements.populationTrend) {
            const trendText = {
                'increasing': '📈 Creciente',
                'decreasing': '📉 Decreciente',
                'stable': '➡️ Estable'
            };
            elements.populationTrend.textContent = trendText[analysis.population.trend] || analysis.population.trend;
        }
        
        if (elements.resourceStability) {
            const correlation = Math.abs(analysis.correlation);
            const stability = correlation > 0.7 ? 'Alta' : correlation > 0.4 ? 'Media' : 'Baja';
            elements.resourceStability.textContent = stability;
        }
    }
    
    console.log('✅ Sistema de gráficos inicializado completamente');
});