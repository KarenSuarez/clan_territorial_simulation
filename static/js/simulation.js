// simulation.js - Versión completa corregida con estado dinámico, formas de especies y rejilla
console.log('🚀 Iniciando simulación.js...');

document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 DOM cargado, configurando simulación...');
    // Elementos del DOM
    const gridCanvas = document.getElementById('gridCanvas');
    const ctx = gridCanvas ? gridCanvas.getContext('2d') : null;

    if (!ctx) {
        console.error('❌ No se pudo obtener el contexto del canvas');
        return;
    }

    // Botones de control
    const playButton = document.getElementById('playButton');
    const pauseButton = document.getElementById('pauseButton');
    const resetButton = document.getElementById('resetButton');
    const stepButton = document.getElementById('stepButton');

    // Elementos de visualización
    const populationDisplay = document.getElementById('population');
    const totalResourceDisplay = document.getElementById('totalResource');
    const stepCountDisplay = document.getElementById('stepCount');
    const timeElapsedDisplay = document.getElementById('timeElapsed');
    const simulationStatus = document.getElementById('simulationStatus');
    const statusIndicator = document.getElementById('statusIndicator');
    const modeDisplay = document.getElementById('modeDisplay');

    // Elementos de control
    const speedSlider = document.getElementById('speedSlider');
    const speedValue = document.getElementById('speedValue');
    const autoResetCheckbox = document.getElementById('autoReset');
    const maxStepsInput = document.getElementById('maxStepsInput');
    const simulationModeSelect = document.getElementById('simulation_mode');
    const configFileSelect = document.getElementById('config_file');
    const seedInput = document.getElementById('seed');

    // Estado de la simulación
    let simulationData = null;
    let simulationRunning = false;
    let cellSize = 12;
    let socket = null;
    let currentSpeed = 1.0;
    let maxSteps = 500;
    let autoStop = true;
    let chartUpdateCounter = 0;
    let lastChartUpdate = 0;
    let currentGridSize = [50, 50]; // NUEVO: Seguimiento del tamaño actual de rejilla

    // NUEVO: Formas de especies para los clanes
    const clanSpecies = {
        1: { name: 'Lobos', shape: 'wolf', color: '#8B4513', emoji: '🐺' },
        2: { name: 'Águilas', shape: 'eagle', color: '#4682B4', emoji: '🦅' },
        3: { name: 'Osos', shape: 'bear', color: '#654321', emoji: '🐻' },
        4: { name: 'Leones', shape: 'lion', color: '#DAA520', emoji: '🦁' },
        5: { name: 'Tigres', shape: 'tiger', color: '#FF4500', emoji: '🐅' },
        6: { name: 'Leopardos', shape: 'leopard', color: '#9370DB', emoji: '🐆' },
        7: { name: 'Zorros', shape: 'fox', color: '#FF6347', emoji: '🦊' },
        8: { name: 'Halcones', shape: 'falcon', color: '#2F4F4F', emoji: '🦉' },
        9: { name: 'Panteras', shape: 'panther', color: '#191970', emoji: '🐈‍⬛' },
        10: { name: 'Coyotes', shape: 'coyote', color: '#A0522D', emoji: '🐕' }
    };

    // Colores para estados de clanes
    const stateColors = {
        'foraging': '#27ae60',    // Verde
        'migrating': '#f39c12',   // Naranja
        'resting': '#9b59b6',     // Púrpura
        'fighting': '#e74c3c',    // Rojo
        'defending': '#3498db'    // Azul
    };

    // Inicializar
    init();

    function init() {
        console.log('⚙️ Inicializando simulación...');

        setupSocket();
        setupEventListeners();
        setupConfigurationHandlers();
        updateCanvasSize();
        updateButtonStates();
        updateStatusIndicator(false);
        startStatusMonitoring();
        initializeChartsIntegration();

        console.log('✅ Simulación inicializada');
    }

    function setupSocket() {
        console.log('🔌 Configurando WebSocket...');

        try {
            socket = io.connect();

            socket.on('connect', () => {
                console.log('✅ WebSocket conectado');
                updateConnectionStatus(true);
                if (window.updateConnectionIndicator) {
                    window.updateConnectionIndicator(true);
                }
                socket.emit('request_state');
                socket.emit('get_available_configs');
            });

            socket.on('disconnect', () => {
                console.log('❌ WebSocket desconectado');
                updateConnectionStatus(false);
                if (window.updateConnectionIndicator) {
                    window.updateConnectionIndicator(false);
                }
                simulationRunning = false;
                updateStatusIndicator(false);
                updateButtonStates();

                setTimeout(() => {
                    if (!socket.connected) {
                        handleReconnection();
                    }
                }, 2000);
            });

            socket.on('simulation_state', (data) => {
                console.log('📥 Estado recibido:', data);
                console.log(`📊 Datos: paso=${data.step}, clanes=${data.clanes ? data.clanes.length : 0}, running=${data.running}`);
                console.log('📊 Métricas del sistema:', data.system_metrics);
                handleSimulationState(data);
            });

            socket.on('simulation_started', (data) => {
                console.log('▶️ Confirmación de inicio recibida');
                simulationRunning = true;
                updateStatusIndicator(true);
                updateButtonStates();
            });

            socket.on('simulation_terminated', (data) => {
                console.log('🏁 Simulación terminada:', data.reason);
                simulationRunning = false;
                updateStatusIndicator(false);
                updateButtonStates();
                showNotification(`Simulación terminada: ${data.reason}`, 'warning', 5000);
            });

            socket.on('simulation_error', (error) => {
                console.error('❌ Error de simulación:', error);
                showNotification('Error: ' + error.error, 'error');
                simulationRunning = false;
                updateStatusIndicator(false);
                updateButtonStates();
            });

            // EVENTOS PARA CONFIGURACIÓN
            socket.on('configuration_applied', (data) => {
                console.log('✅ Configuración aplicada exitosamente:', data.message);
                if (window.setApplyButtonLoading) {
                    window.setApplyButtonLoading(false);
                }
                showNotification(data.message, 'success', 4000);

                if (data.new_state) {
                    handleSimulationState(data.new_state);
                }

                if (data.config && window.updateCurrentConfigInfo) {
                    window.updateCurrentConfigInfo(data.config);
                }
            });

            socket.on('configuration_error', (data) => {
                console.error('❌ Error en configuración:', data.error);
                if (window.setApplyButtonLoading) {
                    window.setApplyButtonLoading(false);
                }
                showNotification('Error: ' + data.error, 'error', 6000);
            });

            socket.on('available_configs', (data) => {
                console.log('📋 Configuraciones disponibles recibidas:', data.configs);
                updateConfigSelect(data.configs);
            });

            socket.on('speed_updated', (data) => {
                console.log('⚡ Velocidad actualizada en servidor:', data.speed);
                currentSpeed = data.speed;
                updateSpeedDisplay();
            });

            socket.on('current_speed', (data) => {
                console.log('📥 Velocidad actual recibida:', data.speed);
                currentSpeed = data.speed;
                updateSpeedDisplay();
            });

            socket.on('simulation_config', (config) => {
                console.log('📥 Configuración recibida:', config);
                maxSteps = config.max_steps || 500;
                autoStop = config.auto_stop !== undefined ? config.auto_stop : true;
                
                // NUEVO: Actualizar tamaño de rejilla
                if (config.grid_size) {
                    currentGridSize = config.grid_size;
                    updateGridSizeDisplay();
                }
                
                updateControlsDisplay();
            });

            // NUEVO: Eventos para tamaño de rejilla
            socket.on('grid_size_updated', (data) => {
                console.log('📐 Tamaño de rejilla actualizado:', data.message);
                
                // Restaurar botón
                const button = document.getElementById('applyGridBtn');
                if (button) {
                    button.disabled = false;
                    button.textContent = '🚀 Aplicar Nuevo Tamaño de Rejilla';
                }
                
                // Actualizar estado
                if (data.new_grid_size) {
                    currentGridSize = data.new_grid_size;
                    updateGridSizeDisplay();
                }
                
                if (data.new_state) {
                    handleSimulationState(data.new_state);
                }
                
                showNotification(data.message, 'success', 4000);
            });

            socket.on('grid_size_error', (data) => {
                console.error('❌ Error actualizando rejilla:', data.error);
                
                // Restaurar botón
                const button = document.getElementById('applyGridBtn');
                if (button) {
                    button.disabled = false;
                    button.textContent = '🚀 Aplicar Nuevo Tamaño de Rejilla';
                }
                
                showNotification('Error: ' + data.error, 'error', 5000);
            });

            // Eventos de parámetros
            setupParameterWebSocketEvents();

            // Solicitar configuración inicial
            socket.emit('get_speed');
            socket.emit('get_simulation_config');

        } catch (error) {
            console.error('❌ Error configurando WebSocket:', error);
        }
    }

    function setupConfigurationHandlers() {
        console.log('⚙️ Configurando manejadores de configuración...');

        const configForm = document.querySelector('.config-form');
        if (configForm) {
            configForm.addEventListener('submit', function (e) {
                e.preventDefault();
                applyConfigurationViaSocket();
            });
        }

        const applyButton = document.querySelector('button[type="submit"]');
        if (applyButton) {
            applyButton.textContent = '🚀 Aplicar Configuración (WebSocket)';
        }
    }

    function applyConfigurationViaSocket() {
        console.log('📡 Aplicando configuración vía WebSocket...');

        if (!socket || !socket.connected) {
            showNotification('Error: Cliente WebSocket desconectado. No se puede aplicar la configuración.', 'error');
            return;
        }

        const formData = {
            simulation_mode: document.getElementById('simulation_mode')?.value || 'stochastic',
            config_file: document.getElementById('config_file')?.value || 'stochastic_default',
            seed: document.getElementById('seed')?.value || null
        };

        console.log('📤 Enviando configuración:', formData);

        if (window.setApplyButtonLoading) {
            window.setApplyButtonLoading(true);
        }
        showNotification('Aplicando configuración...', 'info');

        socket.emit('apply_configuration', formData);
    }

    function updateFormControls(config) {
        console.log('🔄 Actualizando controles del formulario:', config);

        const modeSelect = document.getElementById('simulation_mode');
        const configSelect = document.getElementById('config_file');
        const seedInput = document.getElementById('seed');

        if (modeSelect && config.mode) {
            modeSelect.value = config.mode;
        }

        if (configSelect && config.config_file) {
            configSelect.value = config.config_file;
        }

        if (seedInput && config.seed !== undefined) {
            seedInput.value = config.seed || '';
        }
    }

    function updateConfigSelect(configs) {
        const configSelect = document.getElementById('config_file');
        if (!configSelect || !configs) return;

        configSelect.innerHTML = '';

        configs.forEach(config => {
            const option = document.createElement('option');
            option.value = config;
            option.textContent = config.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
            configSelect.appendChild(option);
        });
    }

    function handleReconnection() {
        console.log('🔄 Intentando reconectar WebSocket...');

        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5;

        const reconnectInterval = setInterval(() => {
            if (socket && socket.connected) {
                console.log('✅ WebSocket reconectado exitosamente');
                clearInterval(reconnectInterval);
                updateConnectionStatus(true);
                showNotification('Reconectado al servidor', 'success');

                socket.emit('request_state');
                socket.emit('get_available_configs');

                return;
            }

            reconnectAttempts++;
            console.log(`🔄 Intento de reconexión ${reconnectAttempts}/${maxReconnectAttempts}`);

            if (reconnectAttempts >= maxReconnectAttempts) {
                console.error('❌ No se pudo reconectar después de varios intentos');
                clearInterval(reconnectInterval);
                showNotification('No se pudo reconectar. Recarga la página.', 'error', 10000);
                return;
            }

            try {
                socket = io.connect();
                setupSocket();
            } catch (error) {
                console.error('❌ Error en intento de reconexión:', error);
            }

        }, 2000);
    }

    function setupEventListeners() {
        console.log('🎮 Configurando controles...');

        if (playButton) {
            playButton.addEventListener('click', () => {
                console.log('👆 Botón INICIAR presionado');
                startSimulation();
            });
        }

        if (pauseButton) {
            pauseButton.addEventListener('click', () => {
                console.log('👆 Botón PAUSAR presionado');
                pauseSimulation();
            });
        }

        if (resetButton) {
            resetButton.addEventListener('click', () => {
                console.log('👆 Botón REINICIAR presionado');
                resetSimulation();
            });
        }

        if (stepButton) {
            stepButton.addEventListener('click', () => {
                console.log('👆 Botón PASO presionado');
                stepSimulation();
            });
        }

        if (speedSlider) {
            speedSlider.addEventListener('input', () => {
                console.log('🎚️ Slider de velocidad cambiado:', speedSlider.value);
                updateSimulationSpeed();
            });
        }

        if (autoResetCheckbox) {
            autoResetCheckbox.addEventListener('change', () => {
                console.log('🔄 Auto-stop toggled:', autoResetCheckbox.checked);
                toggleAutoStop();
            });
        }

        if (maxStepsInput) {
            maxStepsInput.addEventListener('change', updateMaxSteps);
        }

        if (simulationModeSelect) {
            simulationModeSelect.addEventListener('change', function () {
                localStorage.setItem('sim_mode', this.value);
                if (this.value === 'deterministic' && !seedInput.value) {
                    seedInput.value = Math.floor(Math.random() * 999999) + 1;
                }
            });
            const savedMode = localStorage.getItem('sim_mode');
            if (savedMode && simulationModeSelect.querySelector(`option[value="${savedMode}"]`)) {
                simulationModeSelect.value = savedMode;
            }
        }

        if (configFileSelect) {
            configFileSelect.addEventListener('change', function () {
                localStorage.setItem('sim_config', this.value);
            });
            const savedConfig = localStorage.getItem('sim_config');
            if (savedConfig && configFileSelect.querySelector(`option[value="${savedConfig}"]`)) {
                configFileSelect.value = savedConfig;
            }
        }

        // Atajos de teclado
        document.addEventListener('keydown', (event) => {
            if (event.target.tagName === 'INPUT') return;

            switch (event.key) {
                case ' ':
                    event.preventDefault();
                    if (simulationRunning) {
                        pauseSimulation();
                    } else {
                        startSimulation();
                    }
                    break;
                case 'r':
                    event.preventDefault();
                    resetSimulation();
                    break;
                case 's':
                    event.preventDefault();
                    stepSimulation();
                    break;
            }
        });
    }

    function handleSimulationState(data) {
        console.log(`📥 Estado recibido: ${data.clans ? data.clans.length : 0} clanes, paso ${data.step}, modo ${data.mode}`);

        simulationData = data;

        simulationRunning = data.running || false;
        maxSteps = data.max_steps || maxSteps;
        autoStop = data.auto_stop !== undefined ? data.auto_stop : true;

        // NUEVO: Actualizar tamaño de rejilla si viene en los datos
        if (data.grid_size) {
            currentGridSize = data.grid_size;
            updateGridSizeDisplay();
        }

        updateStatusIndicator(simulationRunning);
        updateButtonStates();

        renderSimulation();
        updateMetrics();
        updateClanMetrics();
        updateProgressIndicator();
        updateControlsDisplay();
        updateChartsWithSimulationData();
    }

    function updateStatusIndicator(isRunning) {
        console.log(`🔄 Actualizando estado visual: ${isRunning ? 'Ejecutando' : 'Detenido'}`);

        if (statusIndicator) {
            statusIndicator.className = `status-indicator ${isRunning ? 'status-running' : 'status-stopped'}`;
        }

        if (simulationStatus) {
            simulationStatus.textContent = isRunning ? 'Ejecutando' : 'Detenido';
        }
    }

    function startSimulation() {
        console.log('▶️ Iniciando simulación...');

        if (!socket || !socket.connected) {
            showNotification('No hay conexión con el servidor', 'error');
            return;
        }

        socket.emit('start_simulation');

        simulationRunning = true;
        updateStatusIndicator(true);
        updateButtonStates();

        showNotification('Simulación iniciada', 'success');
    }

    function pauseSimulation() {
        console.log('⏸️ Pausando simulación...');

        simulationRunning = false;
        if (socket) socket.emit('pause_simulation');

        updateStatusIndicator(false);
        updateButtonStates();

        showNotification('Simulación pausada', 'info');
    }

    function resetSimulation() {
        console.log('🔄 Reiniciando simulación...');

        simulationRunning = false;
        if (socket) socket.emit('reset_simulation');

        updateStatusIndicator(false);
        updateButtonStates();
        resetChartsOnSimulationReset();

        showNotification('Simulación reiniciada', 'info');
    }

    function stepSimulation() {
        console.log('👆 Ejecutando paso manual...');

        if (socket) socket.emit('step_simulation');
        showNotification('Paso ejecutado', 'info');
    }

    function startStatusMonitoring() {
        console.log('👁️ Iniciando monitoreo de estado...');

        setInterval(() => {
            if (socket && socket.connected) {
                socket.emit('request_state');
            }
        }, 3000);
    }

    function toggleAutoStop() {
        if (!autoResetCheckbox) return;

        autoStop = autoResetCheckbox.checked;
        if (socket) {
            socket.emit('toggle_auto_stop', { auto_stop: autoStop });
        }

        console.log(`🔄 Auto-stop ${autoStop ? 'activado' : 'desactivado'}`);
        showNotification(`Auto-stop ${autoStop ? 'activado' : 'desactivado'}`, 'info');
    }

    function updateSimulationSpeed() {
        if (!speedSlider || !socket) return;

        const sliderValue = parseInt(speedSlider.value);
        let speedMultiplier;

        if (sliderValue <= 100) {
            speedMultiplier = (sliderValue / 100) * 0.9 + 0.1;
        } else {
            speedMultiplier = 1.0 + ((sliderValue - 100) / 100) * 4.0;
        }

        console.log(`🎚️ Actualizando velocidad: slider=${sliderValue}, speed=${speedMultiplier.toFixed(1)}x`);

        socket.emit('update_speed', { speed: speedMultiplier });

        currentSpeed = speedMultiplier;
        updateSpeedDisplay();
    }

    function updateSpeedDisplay() {
        if (speedValue) {
            speedValue.textContent = `${currentSpeed.toFixed(1)}x`;

            if (currentSpeed < 0.5) {
                speedValue.style.color = '#e74c3c';
            } else if (currentSpeed < 1.0) {
                speedValue.style.color = '#f39c12';
            } else if (currentSpeed <= 1.5) {
                speedValue.style.color = '#27ae60';
            } else {
                speedValue.style.color = '#3498db';
            }
        }

        if (speedSlider && Math.abs(currentSpeed - getSliderSpeed()) > 0.1) {
            updateSliderFromSpeed();
        }
    }

    function getSliderSpeed() {
        if (!speedSlider) return 1.0;

        const sliderValue = parseInt(speedSlider.value);
        if (sliderValue <= 100) {
            return (sliderValue / 100) * 0.9 + 0.1;
        } else {
            return 1.0 + ((sliderValue - 100) / 100) * 4.0;
        }
    }

    function updateSliderFromSpeed() {
        if (!speedSlider) return;

        let sliderValue;
        if (currentSpeed <= 1.0) {
            sliderValue = Math.round(((currentSpeed - 0.1) / 0.9) * 100);
        } else {
            sliderValue = Math.round(100 + ((currentSpeed - 1.0) / 4.0) * 100);
        }

        speedSlider.value = Math.max(1, Math.min(200, sliderValue));
    }

    function updateProgressIndicator() {
        const progressContainer = document.querySelector('.simulation-progress');
        if (progressContainer && simulationData) {
            const progress = (simulationData.step / (simulationData.max_steps || maxSteps)) * 100;

            let progressHTML = `
                <div style="margin: 1rem 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-weight: 600;">Progreso de Simulación</span>
                        <span style="font-size: 0.9rem; color: #666;">${simulationData.step}/${simulationData.max_steps || maxSteps} pasos</span>
                    </div>
                    <div style="background: #e0e0e0; border-radius: 10px; height: 8px; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, #27ae60, #3498db); height: 100%; width: ${Math.min(100, progress)}%; transition: width 0.3s ease;"></div>
                    </div>
                </div>
            `;

            progressContainer.innerHTML = progressHTML;
        }
    }

    function updateControlsDisplay() {
        if (autoResetCheckbox) {
            autoResetCheckbox.checked = autoStop;
        }

        if (maxStepsInput) {
            maxStepsInput.value = maxSteps;
        }

        if (modeDisplay && simulationData && simulationData.mode) {
            modeDisplay.textContent = simulationData.mode.charAt(0).toUpperCase() + simulationData.mode.slice(1);
        }

        if (seedInput && simulationData && simulationData.current_seed !== undefined) {
            seedInput.value = simulationData.current_seed === null ? '' : simulationData.current_seed;
        }

        if (simulationData && simulationData.current_mode) {
            const modeSelect = document.getElementById('simulation_mode');
            if (modeSelect && modeSelect.querySelector(`option[value="${simulationData.current_mode}"]`)) {
                modeSelect.value = simulationData.current_mode;
            }
        }
        if (simulationData && simulationData.current_config_file) {
            const configSelect = document.getElementById('config_file');
            if (configSelect && configSelect.querySelector(`option[value="${simulationData.current_config_file}"]`)) {
                configSelect.value = simulationData.current_config_file;
            }
        }
    }

    // NUEVA FUNCIÓN: Actualizar display del tamaño de rejilla
    function updateGridSizeDisplay() {
        const gridSizeElement = document.getElementById('currentGridSize');
        if (gridSizeElement && currentGridSize) {
            gridSizeElement.textContent = `${currentGridSize[0]}×${currentGridSize[1]}`;
        }

        // También actualizar los controles de rejilla en el panel de parámetros
        const gridWidth = document.getElementById('gridWidth');
        const gridWidthNum = document.getElementById('gridWidthNum');
        const gridHeight = document.getElementById('gridHeight');
        const gridHeightNum = document.getElementById('gridHeightNum');

        if (gridWidth && currentGridSize) {
            gridWidth.value = currentGridSize[0];
        }
        if (gridWidthNum && currentGridSize) {
            gridWidthNum.value = currentGridSize[0];
        }
        if (gridHeight && currentGridSize) {
            gridHeight.value = currentGridSize[1];
        }
        if (gridHeightNum && currentGridSize) {
            gridHeightNum.value = currentGridSize[1];
        }

        // Actualizar vista previa si existe la función
        if (typeof window.updateGridPreview === 'function') {
            window.updateGridPreview();
        }
    }

    function setMaxSteps(newMaxSteps) {
        if (socket) {
            socket.emit('set_max_steps', { max_steps: newMaxSteps });
        }
        maxSteps = newMaxSteps;
    }

    function updateCanvasSize() {
        if (!simulationData || !simulationData.resource_grid) {
            gridCanvas.width = 600;
            gridCanvas.height = 600;
            cellSize = 12;
            return;
        }

        const rows = simulationData.resource_grid.length;
        const cols = simulationData.resource_grid[0].length;

        const containerWidth = gridCanvas.parentElement.clientWidth - 40;
        const maxSize = Math.min(600, containerWidth);

        cellSize = Math.max(8, Math.min(16, maxSize / cols));

        gridCanvas.width = cols * cellSize;
        gridCanvas.height = rows * cellSize;

        console.log(`📐 Canvas: ${gridCanvas.width}x${gridCanvas.height}, celda: ${cellSize}px`);
    }

    function renderSimulation() {
        if (!simulationData || !ctx) {
            console.warn('⚠️ Sin datos de simulación o contexto de canvas');
            return;
        }

        const grid = simulationData.resource_grid;
        const clans = simulationData.clans || [];

        if (!grid || grid.length === 0) {
            console.warn('⚠️ No hay datos de grid para renderizar');
            return;
        }

        updateCanvasSize();

        const rows = grid.length;
        const cols = grid[0].length;

        console.log(`🎨 Renderizando: ${rows}x${cols} grid, ${clans.length} clanes`);

        ctx.clearRect(0, 0, gridCanvas.width, gridCanvas.height);

        renderResources(grid, rows, cols);
        renderClans(clans);

        if (cellSize > 10) {
            renderGrid(rows, cols);
        }

        console.log('✅ Renderizado completado');
    }

    function renderResources(grid, rows, cols) {
        for (let y = 0; y < rows; y++) {
            for (let x = 0; x < cols; x++) {
                const resource = grid[y][x];
                const intensity = Math.min(1, Math.max(0, resource / 100));

                ctx.fillStyle = `rgba(34, 139, 34, ${intensity * 0.6})`;
                ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
            }
        }
    }

    function exportChartData() {
        if (!window.ChartController) {
            showNotification('Gráficos no disponibles para exportar', 'error');
            return;
        }

        try {
            const chartData = window.ChartController.getChartData();
            const analysis = window.ChartController.generateTrendAnalysis();

            const exportData = {
                metadata: {
                    export_time: new Date().toISOString(),
                    data_points: chartData.labels.length,
                    max_data_points: chartData.maxDataPoints
                },
                chart_data: chartData,
                trend_analysis: analysis,
                simulation_info: {
                    current_step: simulationData?.step || 0,
                    current_mode: simulationData?.mode || 'unknown',
                    running: simulationRunning
                }
            };

            const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `chart_data_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            showNotification('Datos de gráficos exportados exitosamente', 'success');

        } catch (error) {
            console.error('❌ Error exportando datos de gráficos:', error);
            showNotification('Error exportando datos de gráficos', 'error');
        }
    }

    function showTrendAnalysis() {
        if (!window.ChartController) {
            showNotification('Análisis no disponible', 'error');
            return;
        }

        try {
            const analysis = window.ChartController.generateTrendAnalysis();

            if (analysis.status === 'insufficient_data') {
                showNotification(analysis.message, 'warning');
                return;
            }

            let analysisText = `
📊 ANÁLISIS DE TENDENCIAS

👥 POBLACIÓN:
• Tendencia: ${analysis.population.trend}
• Promedio: ${analysis.population.average.toFixed(1)}
• Máximo: ${analysis.population.max}
• Mínimo: ${analysis.population.min}
• Actual: ${analysis.population.current}

🌿 RECURSOS:
• Tendencia: ${analysis.resources.trend}
• Promedio: ${analysis.resources.average.toFixed(1)}
• Máximo: ${analysis.resources.max.toFixed(1)}
• Mínimo: ${analysis.resources.min.toFixed(1)}
• Actual: ${analysis.resources.current.toFixed(1)}

🔗 CORRELACIÓN: ${analysis.correlation.toFixed(3)}
        `;

            const modal = document.createElement('div');
            modal.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            z-index: 10000;
            max-width: 500px;
            max-height: 80vh;
            overflow-y: auto;
        `;

            modal.innerHTML = `
            <h3 style="margin-top: 0;">📊 Análisis de Tendencias</h3>
            <pre style="font-family: monospace; font-size: 0.9rem; line-height: 1.4; white-space: pre-wrap;">${analysisText}</pre>
            <button onclick="this.parentElement.remove()" style="margin-top: 1rem; padding: 0.5rem 1rem; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer;">Cerrar</button>
        `;

            document.body.appendChild(modal);

            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.remove();
                }
            });

        } catch (error) {
            console.error('❌ Error generando análisis:', error);
            showNotification('Error generando análisis de tendencias', 'error');
        }
    }

    // NUEVA FUNCIÓN: Renderizar clanes con formas de especies
    function renderClans(clans) {
        clans.forEach((clan) => {
            const x = clan.position[0] * cellSize + cellSize / 2;
            const y = clan.position[1] * cellSize + cellSize / 2;
            const baseRadius = Math.max(4, Math.min(cellSize / 2, clan.visual_size || Math.sqrt(clan.size) * 1.5));

            // Obtener información de la especie
            const species = clanSpecies[clan.id] || clanSpecies[1]; // Default a Lobos si no existe
            const stateColor = stateColors[clan.state] || '#95a5a6';

            // Dibujar forma de la especie
            drawSpeciesShape(ctx, species.shape, x, y, baseRadius, species.color, stateColor, clan.size);

            // Barra de energía
            if (cellSize > 12 && clan.energy !== undefined) {
                drawEnergyBar(x, y - baseRadius - 8, baseRadius * 2, clan.energy);
            }

            // Emoji de la especie (si el tamaño lo permite)
            if (cellSize > 14) {
                drawSpeciesEmoji(ctx, species.emoji, x, y + baseRadius + 12, cellSize * 0.6);
            }
        });
    }

    // NUEVA FUNCIÓN: Dibujar formas de especies
    function drawSpeciesShape(ctx, shape, x, y, radius, speciesColor, stateColor, size) {
        ctx.save();
        
        switch (shape) {
            case 'wolf':
                drawWolfShape(ctx, x, y, radius, speciesColor, stateColor);
                break;
            case 'eagle':
                drawEagleShape(ctx, x, y, radius, speciesColor, stateColor);
                break;
            case 'bear':
                drawBearShape(ctx, x, y, radius, speciesColor, stateColor);
                break;
            case 'lion':
                drawLionShape(ctx, x, y, radius, speciesColor, stateColor);
                break;
            case 'tiger':
                drawTigerShape(ctx, x, y, radius, speciesColor, stateColor);
                break;
            case 'leopard':
                drawLeopardShape(ctx, x, y, radius, speciesColor, stateColor);
                break;
            case 'fox':
                drawFoxShape(ctx, x, y, radius, speciesColor, stateColor);
                break;
            case 'falcon':
                drawFalconShape(ctx, x, y, radius, speciesColor, stateColor);
                break;
            case 'panther':
                drawPantherShape(ctx, x, y, radius, speciesColor, stateColor);
                break;
            case 'coyote':
                drawCoyoteShape(ctx, x, y, radius, speciesColor, stateColor);
                break;
            default:
                // Forma por defecto (círculo)
                drawDefaultShape(ctx, x, y, radius, speciesColor, stateColor);
                break;
        }

        // Dibujar número de tamaño
        if (cellSize > 10) {
            ctx.fillStyle = 'white';
            ctx.font = `bold ${Math.max(8, cellSize * 0.3)}px Arial`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.strokeStyle = 'black';
            ctx.lineWidth = 1;
            ctx.strokeText(size.toString(), x, y);
            ctx.fillText(size.toString(), x, y);
        }
        
        ctx.restore();
    }

    // Formas específicas para cada especie
    function drawWolfShape(ctx, x, y, radius, speciesColor, stateColor) {
        // Cuerpo principal (elipse)
        ctx.beginPath();
        ctx.ellipse(x, y, radius * 1.2, radius * 0.8, 0, 0, 2 * Math.PI);
        ctx.fillStyle = createGradient(ctx, x, y, radius, speciesColor, stateColor);
        ctx.fill();
        ctx.strokeStyle = adjustColor(speciesColor, -40);
        ctx.lineWidth = 2;
        ctx.stroke();

        // Orejas puntiagudas
        ctx.beginPath();
        ctx.moveTo(x - radius * 0.6, y - radius * 0.5);
        ctx.lineTo(x - radius * 0.3, y - radius * 1.2);
        ctx.lineTo(x - radius * 0.1, y - radius * 0.7);
        ctx.moveTo(x + radius * 0.1, y - radius * 0.7);
        ctx.lineTo(x + radius * 0.3, y - radius * 1.2);
        ctx.lineTo(x + radius * 0.6, y - radius * 0.5);
        ctx.fillStyle = speciesColor;
        ctx.fill();
        ctx.stroke();
    }

    function drawEagleShape(ctx, x, y, radius, speciesColor, stateColor) {
        // Cuerpo (óvalo vertical)
        ctx.beginPath();
        ctx.ellipse(x, y, radius * 0.7, radius * 1.3, 0, 0, 2 * Math.PI);
        ctx.fillStyle = createGradient(ctx, x, y, radius, speciesColor, stateColor);
        ctx.fill();
        ctx.strokeStyle = adjustColor(speciesColor, -40);
        ctx.lineWidth = 2;
        ctx.stroke();

        // Alas extendidas
        ctx.beginPath();
        ctx.ellipse(x - radius * 1.2, y, radius * 0.8, radius * 0.4, -Math.PI/6, 0, 2 * Math.PI);
        ctx.ellipse(x + radius * 1.2, y, radius * 0.8, radius * 0.4, Math.PI/6, 0, 2 * Math.PI);
        ctx.fillStyle = adjustColor(speciesColor, -20);
        ctx.fill();
        ctx.stroke();

        // Pico
        ctx.beginPath();
        ctx.moveTo(x, y - radius * 1.3);
        ctx.lineTo(x - radius * 0.3, y - radius * 1.6);
        ctx.lineTo(x + radius * 0.3, y - radius * 1.6);
        ctx.closePath();
        ctx.fillStyle = '#FFA500';
        ctx.fill();
    }

    function drawBearShape(ctx, x, y, radius, speciesColor, stateColor) {
        // Cuerpo robusto (círculo grande)
        ctx.beginPath();
        ctx.arc(x, y, radius * 1.3, 0, 2 * Math.PI);
        ctx.fillStyle = createGradient(ctx, x, y, radius, speciesColor, stateColor);
        ctx.fill();
        ctx.strokeStyle = adjustColor(speciesColor, -40);
        ctx.lineWidth = 3;
        ctx.stroke();

        // Orejas redondas
        ctx.beginPath();
        ctx.arc(x - radius * 0.7, y - radius * 0.9, radius * 0.4, 0, 2 * Math.PI);
        ctx.arc(x + radius * 0.7, y - radius * 0.9, radius * 0.4, 0, 2 * Math.PI);
        ctx.fillStyle = speciesColor;
        ctx.fill();
        ctx.stroke();

        // Hocico
        ctx.beginPath();
        ctx.ellipse(x, y + radius * 0.6, radius * 0.5, radius * 0.3, 0, 0, 2 * Math.PI);
        ctx.fillStyle = adjustColor(speciesColor, 20);
        ctx.fill();
    }

    function drawLionShape(ctx, x, y, radius, speciesColor, stateColor) {
        // Cuerpo
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, 2 * Math.PI);
        ctx.fillStyle = createGradient(ctx, x, y, radius, speciesColor, stateColor);
        ctx.fill();
        ctx.strokeStyle = adjustColor(speciesColor, -40);
        ctx.lineWidth = 2;
        ctx.stroke();

        // Melena (círculo exterior más claro)
        ctx.beginPath();
        ctx.arc(x, y, radius * 1.4, 0, 2 * Math.PI);
        ctx.fillStyle = adjustColor(speciesColor, 30);
        ctx.fill();

        // Redibuja el cuerpo encima
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, 2 * Math.PI);
        ctx.fillStyle = createGradient(ctx, x, y, radius, speciesColor, stateColor);
        ctx.fill();
        ctx.stroke();
    }

    function drawTigerShape(ctx, x, y, radius, speciesColor, stateColor) {
        // Cuerpo
        ctx.beginPath();
        ctx.ellipse(x, y, radius * 1.1, radius * 0.9, 0, 0, 2 * Math.PI);
        ctx.fillStyle = createGradient(ctx, x, y, radius, speciesColor, stateColor);
        ctx.fill();
        ctx.strokeStyle = adjustColor(speciesColor, -40);
        ctx.lineWidth = 2;
        ctx.stroke();

        // Rayas características
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 2;
        for (let i = -2; i <= 2; i++) {
            ctx.beginPath();
            ctx.moveTo(x + i * radius * 0.3, y - radius * 0.6);
            ctx.lineTo(x + i * radius * 0.3, y + radius * 0.6);
            ctx.stroke();
        }

        // Orejas puntiagudas
        ctx.beginPath();
        ctx.moveTo(x - radius * 0.6, y - radius * 0.5);
        ctx.lineTo(x - radius * 0.4, y - radius * 1.1);
        ctx.lineTo(x - radius * 0.2, y - radius * 0.7);
        ctx.moveTo(x + radius * 0.2, y - radius * 0.7);
        ctx.lineTo(x + radius * 0.4, y - radius * 1.1);
        ctx.lineTo(x + radius * 0.6, y - radius * 0.5);
        ctx.fillStyle = speciesColor;
        ctx.fill();
    }

    function drawLeopardShape(ctx, x, y, radius, speciesColor, stateColor) {
        // Cuerpo elegante
        ctx.beginPath();
        ctx.ellipse(x, y, radius * 1.1, radius * 0.8, 0, 0, 2 * Math.PI);
        ctx.fillStyle = createGradient(ctx, x, y, radius, speciesColor, stateColor);
        ctx.fill();
        ctx.strokeStyle = adjustColor(speciesColor, -40);
        ctx.lineWidth = 2;
        ctx.stroke();

        // Manchas características
        ctx.fillStyle = '#000000';
        const spots = [
            [-0.4, -0.3], [0.4, -0.3], [-0.2, 0.1], [0.2, 0.1], [0, 0.4]
        ];
        spots.forEach(([dx, dy]) => {
            ctx.beginPath();
            ctx.arc(x + dx * radius, y + dy * radius, radius * 0.1, 0, 2 * Math.PI);
            ctx.fill();
        });
    }

    function drawFoxShape(ctx, x, y, radius, speciesColor, stateColor) {
        // Cuerpo delgado
        ctx.beginPath();
        ctx.ellipse(x, y, radius * 0.9, radius * 1.1, 0, 0, 2 * Math.PI);
        ctx.fillStyle = createGradient(ctx, x, y, radius, speciesColor, stateColor);
        ctx.fill();
        ctx.strokeStyle = adjustColor(speciesColor, -40);
        ctx.lineWidth = 2;
        ctx.stroke();

        // Orejas grandes y puntiagudas
        ctx.beginPath();
        ctx.moveTo(x - radius * 0.5, y - radius * 0.6);
        ctx.lineTo(x - radius * 0.2, y - radius * 1.3);
        ctx.lineTo(x, y - radius * 0.8);
        ctx.moveTo(x, y - radius * 0.8);
        ctx.lineTo(x + radius * 0.2, y - radius * 1.3);
        ctx.lineTo(x + radius * 0.5, y - radius * 0.6);
        ctx.fillStyle = speciesColor;
        ctx.fill();
        ctx.stroke();

        // Hocico puntiagudo
        ctx.beginPath();
        ctx.moveTo(x, y + radius * 0.6);
        ctx.lineTo(x - radius * 0.2, y + radius * 1.1);
        ctx.lineTo(x + radius * 0.2, y + radius * 1.1);
        ctx.closePath();
        ctx.fillStyle = adjustColor(speciesColor, 20);
        ctx.fill();
    }

    function drawFalconShape(ctx, x, y, radius, speciesColor, stateColor) {
        // Similar al águila pero más compacto
        ctx.beginPath();
        ctx.ellipse(x, y, radius * 0.6, radius * 1.2, 0, 0, 2 * Math.PI);
        ctx.fillStyle = createGradient(ctx, x, y, radius, speciesColor, stateColor);
        ctx.fill();
        ctx.strokeStyle = adjustColor(speciesColor, -40);
        ctx.lineWidth = 2;
        ctx.stroke();

        // Alas más pequeñas
        ctx.beginPath();
        ctx.ellipse(x - radius * 0.9, y, radius * 0.6, radius * 0.3, -Math.PI/4, 0, 2 * Math.PI);
        ctx.ellipse(x + radius * 0.9, y, radius * 0.6, radius * 0.3, Math.PI/4, 0, 2 * Math.PI);
        ctx.fillStyle = adjustColor(speciesColor, -20);
        ctx.fill();
        ctx.stroke();
    }

    function drawPantherShape(ctx, x, y, radius, speciesColor, stateColor) {
        // Cuerpo esbelto y alargado
        ctx.beginPath();
        ctx.ellipse(x, y, radius * 1.2, radius * 0.7, 0, 0, 2 * Math.PI);
        ctx.fillStyle = createGradient(ctx, x, y, radius, speciesColor, stateColor);
        ctx.fill();
        ctx.strokeStyle = adjustColor(speciesColor, -40);
        ctx.lineWidth = 2;
        ctx.stroke();

        // Brillo en los ojos
        ctx.fillStyle = '#00FF00';
        ctx.beginPath();
        ctx.arc(x - radius * 0.3, y - radius * 0.2, radius * 0.08, 0, 2 * Math.PI);
        ctx.arc(x + radius * 0.3, y - radius * 0.2, radius * 0.08, 0, 2 * Math.PI);
        ctx.fill();
    }

    function drawCoyoteShape(ctx, x, y, radius, speciesColor, stateColor) {
        // Similar al lobo pero más delgado
        ctx.beginPath();
        ctx.ellipse(x, y, radius * 1.1, radius * 0.7, 0, 0, 2 * Math.PI);
        ctx.fillStyle = createGradient(ctx, x, y, radius, speciesColor, stateColor);
        ctx.fill();
        ctx.strokeStyle = adjustColor(speciesColor, -40);
        ctx.lineWidth = 2;
        ctx.stroke();

        // Orejas grandes
        ctx.beginPath();
        ctx.moveTo(x - radius * 0.5, y - radius * 0.4);
        ctx.lineTo(x - radius * 0.2, y - radius * 1.1);
        ctx.lineTo(x - radius * 0.1, y - radius * 0.6);
        ctx.moveTo(x + radius * 0.1, y - radius * 0.6);
        ctx.lineTo(x + radius * 0.2, y - radius * 1.1);
        ctx.lineTo(x + radius * 0.5, y - radius * 0.4);
        ctx.fillStyle = speciesColor;
        ctx.fill();
        ctx.stroke();
    }

    function drawDefaultShape(ctx, x, y, radius, speciesColor, stateColor) {
        // Forma por defecto (círculo con gradiente)
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, 2 * Math.PI);
        ctx.fillStyle = createGradient(ctx, x, y, radius, speciesColor, stateColor);
        ctx.fill();
        ctx.strokeStyle = adjustColor(speciesColor, -30);
        ctx.lineWidth = 2;
        ctx.stroke();
    }

    // NUEVA FUNCIÓN: Crear gradiente para las formas
    function createGradient(ctx, x, y, radius, color1, color2) {
        const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
        gradient.addColorStop(0, color1);
        gradient.addColorStop(0.7, color2);
        gradient.addColorStop(1, adjustColor(color1, -30));
        return gradient;
    }

    // NUEVA FUNCIÓN: Dibujar emoji de especie
    function drawSpeciesEmoji(ctx, emoji, x, y, size) {
        ctx.font = `${size}px Arial`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(emoji, x, y);
    }

    function renderGrid(rows, cols) {
        ctx.strokeStyle = 'rgba(0,0,0,0.1)';
        ctx.lineWidth = 1;

        for (let x = 0; x <= cols; x++) {
            ctx.beginPath();
            ctx.moveTo(x * cellSize, 0);
            ctx.lineTo(x * cellSize, rows * cellSize);
            ctx.stroke();
        }

        for (let y = 0; y <= rows; y++) {
            ctx.beginPath();
            ctx.moveTo(0, y * cellSize);
            ctx.lineTo(cols * cellSize, y * cellSize);
            ctx.stroke();
        }
    }

    function drawEnergyBar(x, y, width, energy) {
        const barHeight = 4;
        const energyPercent = energy / 100;

        // Fondo
        ctx.fillStyle = 'rgba(0,0,0,0.3)';
        ctx.fillRect(x - width / 2, y, width, barHeight);

        // Barra de energía
        let color;
        if (energyPercent > 0.6) color = '#27ae60';
        else if (energyPercent > 0.3) color = '#f39c12';
        else color = '#e74c3c';

        ctx.fillStyle = color;
        ctx.fillRect(x - width / 2, y, width * energyPercent, barHeight);

        // Borde
        ctx.strokeStyle = 'rgba(0,0,0,0.5)';
        ctx.lineWidth = 1;
        ctx.strokeRect(x - width / 2, y, width, barHeight);
    }

    function updateMetrics() {
        if (!simulationData) return;

        console.log('📊 Actualizando métricas con datos:', simulationData.system_metrics);

        const totalPop = simulationData.system_metrics?.total_population || 0;
        const totalRes = simulationData.system_metrics?.total_resources || 0;
        const avgEnergy = simulationData.system_metrics?.avg_energy || 0;
        const activeClanCount = simulationData.system_metrics?.active_clans || 0;

        if (populationDisplay) {
            populationDisplay.textContent = Math.round(totalPop);
        }
        if (totalResourceDisplay) {
            totalResourceDisplay.textContent = totalRes.toFixed(1);
        }
        if (stepCountDisplay) {
            stepCountDisplay.textContent = `${simulationData.step || 0}/${maxSteps}`;
        }
        if (timeElapsedDisplay) {
            timeElapsedDisplay.textContent = formatTime(simulationData.time || 0);
        }

        const avgEnergyDisplay = document.getElementById('avgEnergyDisplay');
        if (avgEnergyDisplay) {
            avgEnergyDisplay.textContent = `${avgEnergy.toFixed(1)}%`;
        }

        const activeClanDisplay = document.getElementById('activeClanDisplay');
        if (activeClanDisplay) {
            activeClanDisplay.textContent = activeClanCount;
        }
    }

    function updateClanMetrics() {
        const container = document.getElementById('clanMetrics');
        if (!container || !simulationData?.clans) return;

        if (simulationData.clans.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #666;">No hay clanes activos</p>';
            return;
        }

        let html = '';
        simulationData.clans.forEach((clan) => {
            const species = clanSpecies[clan.id] || clanSpecies[1];
            const stateColor = stateColors[clan.state] || '#95a5a6';
            const stateEmoji = getStateEmoji(clan.state);

            let energyColor = '#27ae60';
            if (clan.energy < 25) energyColor = '#e74c3c';
            else if (clan.energy < 50) energyColor = '#f39c12';

            html += `
                <div class="clan-metric" style="border-left: 4px solid ${species.color}; margin-bottom: 0.5rem; padding: 0.8rem; background: white; border-radius: 4px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>${species.emoji} ${species.name} ${clan.id}</strong>
                        <span>${stateEmoji} ${clan.state}</span>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.3rem; font-size: 0.9rem; margin-top: 0.5rem;">
                        <span>👥 Tamaño: <strong>${Math.round(clan.size)}</strong></span>
                        <span style="color: ${energyColor}">⚡ Energía: <strong>${clan.energy?.toFixed(1)}%</strong></span>
                        <span>📍 X: <strong>${clan.position[0].toFixed(1)}</strong></span>
                        <span>📍 Y: <strong>${clan.position[1].toFixed(1)}</strong></span>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    function updateChartsWithSimulationData() {
        if (!simulationData || !window.ChartController) {
            return;
        }

        chartUpdateCounter++;
        if (chartUpdateCounter < 3) {
            return;
        }
        chartUpdateCounter = 0;

        const currentTime = Date.now();
        if (currentTime - lastChartUpdate < 1000) {
            return;
        }
        lastChartUpdate = currentTime;

        try {
            const step = simulationData.step || 0;
            const population = simulationData.system_metrics?.total_population || 0;
            const resources = simulationData.system_metrics?.total_resources || 0;

            const scaledResources = resources / 100;

            console.log(`📈 Actualizando gráfico: paso=${step}, pop=${population}, res=${scaledResources.toFixed(1)}`);

            window.ChartController.updatePopulationChart(step, population, scaledResources);
            updateTerritorialChart();

        } catch (error) {
            console.error('❌ Error actualizando gráficos:', error);
        }
    }

    function updateTerritorialChart() {
        if (!simulationData?.clans || !window.ChartController.updateSpatialChart) {
            return;
        }

        try {
            const totalCells = simulationData.system_metrics?.grid_size ?
                (simulationData.system_metrics.grid_size[0] * simulationData.system_metrics.grid_size[1]) : 10000;

            let controlledArea = 0;
            simulationData.clans.forEach(clan => {
                controlledArea += clan.territory_size || 0;
            });

            const freeArea = Math.max(0, totalCells - controlledArea);
            const disputedArea = Math.min(controlledArea * 0.1, freeArea * 0.1);

            window.ChartController.updateSpatialChart(controlledArea, freeArea, disputedArea);

        } catch (error) {
            console.error('❌ Error actualizando gráfico territorial:', error);
        }
    }

    function resetChartsOnSimulationReset() {
        console.log('🔄 Reiniciando gráficos...');

        if (window.ChartController) {
            window.ChartController.clearAllCharts();
        }

        chartUpdateCounter = 0;
        lastChartUpdate = 0;
    }

    function initializeChartsIntegration() {
        console.log('📊 Inicializando integración de gráficos...');

        if (typeof Chart === 'undefined') {
            console.warn('⚠️ Chart.js no está disponible, gráficos deshabilitados');
            return;
        }

        if (!window.ChartController) {
            console.warn('⚠️ ChartController no está disponible, esperando...');
            setTimeout(initializeChartsIntegration, 1000);
            return;
        }

        window.ChartController.setMaxDataPoints(100);

        console.log('✅ Integración de gráficos inicializada');
    }

    function updateButtonStates() {
        if (playButton) {
            playButton.disabled = simulationRunning;
            playButton.textContent = simulationRunning ? 'Ejecutando...' : '▶️ Iniciar';
        }

        if (pauseButton) pauseButton.disabled = !simulationRunning;
        if (resetButton) resetButton.disabled = false;
        if (stepButton) stepButton.disabled = simulationRunning;
    }

    function updateConnectionStatus(connected) {
        console.log(`🔌 Estado de conexión: ${connected ? 'Conectado' : 'Desconectado'}`);
    }

    function formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    function getStateEmoji(state) {
        const emojis = {
            'foraging': '🌾',
            'migrating': '🏃',
            'resting': '😴',
            'fighting': '⚔️',
            'defending': '🛡️'
        };
        return emojis[state] || '❓';
    }

    function adjustColor(color, amount) {
        const num = parseInt(color.replace("#", ""), 16);
        const amt = Math.round(2.55 * amount);
        const R = (num >> 16) + amt;
        const G = (num >> 8 & 0x00FF) + amt;
        const B = (num & 0x0000FF) + amt;
        return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
            (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
            (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1);
    }

    function showNotification(message, type = 'info', duration = 3000) {
        console.log(`📢 ${type.toUpperCase()}: ${message}`);

        const notification = document.createElement('div');
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 6px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
            max-width: 300px;
        `;

        const colors = {
            success: '#27ae60',
            error: '#e74c3c',
            warning: '#f39c12',
            info: '#3498db'
        };
        notification.style.backgroundColor = colors[type] || colors.info;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 100);

        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, duration);
    }

    // === EDITOR DE PARÁMETROS ===

    let parameterEditor = {
        isOpen: false,
        currentTab: 'population',
        hasChanges: false,
        autoApply: true,
        parameters: {},
        presets: {}
    };

    function initializeParameterEditor() {
        console.log('🔧 Inicializando editor de parámetros...');

        setupParameterSync();
        loadDefaultParameters();
        loadPresets();

        const autoApplyCheckbox = document.getElementById('autoApply');
        if (autoApplyCheckbox) {
            autoApplyCheckbox.addEventListener('change', (e) => {
                parameterEditor.autoApply = e.target.checked;
                updateApplyButton();
            });
        }

        console.log('✅ Editor de parámetros inicializado');
    }

    function setupParameterSync() {
        const parameterIds = [
            'birthRate', 'deathRate', 'starvationMortality', 'energyDecay',
            'resourceRegen', 'resourceRequired', 'energyConversion', 'resourceMax',
            'cooperation', 'aggressiveness', 'movementSpeed', 'perceptionRadius', 'territorialExpansion',
            'combatRadius', 'combatDamage', 'combatEnergyCost', 'allianceProbability',
            'interactionRadius', 'migrationThreshold', 'restingThreshold', 'fightingThreshold',
            'gridWidth', 'gridHeight' // NUEVOS parámetros de rejilla
        ];

        parameterIds.forEach(id => {
            const slider = document.getElementById(id);
            const numberInput = document.getElementById(id + 'Num');

            if (slider && numberInput) {
                slider.addEventListener('input', (e) => {
                    numberInput.value = e.target.value;
                    onParameterChange(id, parseFloat(e.target.value));
                });

                numberInput.addEventListener('input', (e) => {
                    const value = parseFloat(e.target.value);
                    if (!isNaN(value)) {
                        slider.value = value;
                        onParameterChange(id, value);
                    }
                });

                numberInput.addEventListener('blur', (e) => {
                    validateParameterValue(id, e.target);
                });
            }
        });
    }

    function onParameterChange(parameterId, value) {
        parameterEditor.parameters[parameterId] = value;
        parameterEditor.hasChanges = true;

        const paramGroup = document.getElementById(parameterId)?.closest('.param-group');
        if (paramGroup) {
            paramGroup.classList.add('changed');
            setTimeout(() => paramGroup.classList.remove('changed'), 500);
        }

        // Actualizar vista previa para parámetros de rejilla
        if (parameterId === 'gridWidth' || parameterId === 'gridHeight') {
            if (typeof window.updateGridPreview === 'function') {
                window.updateGridPreview();
            }
        }

        if (parameterEditor.autoApply) {
            debounceApplyParameters();
        } else {
            updateApplyButton();
        }

        console.log(`📝 Parámetro ${parameterId} cambiado a:`, value);
    }

    let applyParametersTimeout;
    function debounceApplyParameters() {
        clearTimeout(applyParametersTimeout);
        applyParametersTimeout = setTimeout(() => {
            applyParameters();
        }, 500);
    }

    function validateParameterValue(parameterId, input) {
        const value = parseFloat(input.value);
        const min = parseFloat(input.min);
        const max = parseFloat(input.max);

        if (isNaN(value)) {
            input.value = parameterEditor.parameters[parameterId] || 0;
            showNotification('Valor no válido', 'error');
            return false;
        }

        if (value < min) {
            input.value = min;
            onParameterChange(parameterId, min);
            showNotification(`Valor mínimo: ${min}`, 'warning');
            return false;
        }

        if (value > max) {
            input.value = max;
            onParameterChange(parameterId, max);
            showNotification(`Valor máximo: ${max}`, 'warning');
            return false;
        }

        return true;
    }

    function toggleParameterPanel() {
        const panel = document.getElementById('parameterEditorPanel');
        const toggleBtn = document.getElementById('parameterToggleBtn');

        if (!panel || !toggleBtn) return;

        parameterEditor.isOpen = !parameterEditor.isOpen;

        if (parameterEditor.isOpen) {
            panel.classList.remove('collapsed');
        } else {
            panel.classList.add('collapsed');
        }

        console.log(`🔧 Panel de parámetros ${parameterEditor.isOpen ? 'abierto' : 'cerrado'}`);
    }

    function showTab(tabName) {
        document.querySelectorAll('.parameter-section').forEach(section => {
            section.classList.remove('active');
        });

        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        const targetSection = document.getElementById(tabName + '-tab');
        const targetBtn = event.target;

        if (targetSection) {
            targetSection.classList.add('active');
            targetBtn.classList.add('active');
            parameterEditor.currentTab = tabName;
        }

        console.log(`📑 Pestaña cambiada a: ${tabName}`);
    }

    function applyParameters() {
        if (!socket || !socket.connected) {
            showNotification('No hay conexión con el servidor', 'error');
            return;
        }

        const applyToExisting = document.getElementById('applyToExisting')?.checked || false;

        updateParameterStatus('applying', 'Aplicando cambios...');

        const parametersToApply = {
            ...parameterEditor.parameters,
            apply_to_existing: applyToExisting
        };

        console.log('📤 Enviando parámetros al servidor:', parametersToApply);

        socket.emit('update_parameters', parametersToApply);

        parameterEditor.hasChanges = false;
        updateApplyButton();
    }

    function updateApplyButton() {
        const applyBtn = document.getElementById('applyBtn');
        if (!applyBtn) return;

        if (parameterEditor.autoApply) {
            applyBtn.style.display = 'none';
        } else {
            applyBtn.style.display = 'block';
            applyBtn.disabled = !parameterEditor.hasChanges;
            applyBtn.textContent = parameterEditor.hasChanges ? '✅ Aplicar Cambios' : '✅ Sin Cambios';
        }
    }

    function updateParameterStatus(type, message) {
        const statusElement = document.getElementById('parameterStatus');
        if (!statusElement) return;

        const indicator = statusElement.querySelector('.status-indicator');
        const text = statusElement.querySelector('.status-text');

        if (indicator && text) {
            indicator.className = `status-indicator ${type}`;
            text.textContent = message;

            const colors = {
                ready: '🟢',
                applying: '🟡',
                success: '🟢',
                error: '🔴'
            };

            indicator.textContent = colors[type] || '🟢';
        }
    }

    function loadDefaultParameters() {
        const defaults = {
            birthRate: 0.1,
            deathRate: 0.05,
            starvationMortality: 0.8,
            energyDecay: 3,
            resourceRegen: 1.5,
            resourceRequired: 1.2,
            energyConversion: 15,
            resourceMax: 100,
            cooperation: 0.6,
            aggressiveness: 0.3,
            movementSpeed: 1,
            perceptionRadius: 5,
            territorialExpansion: 0.05,
            combatRadius: 5,
            combatDamage: 5,
            combatEnergyCost: 20,
            allianceProbability: 0.2,
            interactionRadius: 5,
            migrationThreshold: 10,
            restingThreshold: 25,
            fightingThreshold: 30,
            gridWidth: currentGridSize[0] || 50, // NUEVOS parámetros
            gridHeight: currentGridSize[1] || 50
        };

        parameterEditor.parameters = { ...defaults };
        updateParameterInputs(defaults);
    }

    function updateParameterInputs(parameters) {
        Object.entries(parameters).forEach(([key, value]) => {
            const slider = document.getElementById(key);
            const numberInput = document.getElementById(key + 'Num');

            if (slider) slider.value = value;
            if (numberInput) numberInput.value = value;
        });
    }

    function loadPresets() {
        parameterEditor.presets = {
            aggressive: {
                name: "🔥 Agresivo",
                description: "Combate intenso y territorialidad alta",
                parameters: {
                    aggressiveness: 0.8,
                    cooperation: 0.2,
                    combatDamage: 8,
                    combatEnergyCost: 15,
                    territorialExpansion: 0.15,
                    allianceProbability: 0.05,
                    birthRate: 0.15,
                    deathRate: 0.08
                }
            },
            cooperative: {
                name: "🤝 Cooperativo",
                description: "Alianzas y cooperación maximizada",
                parameters: {
                    cooperation: 0.9,
                    aggressiveness: 0.1,
                    allianceProbability: 0.4,
                    combatDamage: 3,
                    territorialExpansion: 0.02,
                    birthRate: 0.12,
                    energyConversion: 20
                }
            },
            survival: {
                name: "💀 Supervivencia",
                description: "Recursos escasos y supervivencia difícil",
                parameters: {
                    resourceRegen: 0.8,
                    resourceRequired: 2.0,
                    starvationMortality: 0.95,
                    energyDecay: 5,
                    deathRate: 0.08,
                    energyConversion: 10,
                    restingThreshold: 35
                }
            },
            rapid_growth: {
                name: "📈 Crecimiento Rápido",
                description: "Crecimiento poblacional acelerado",
                parameters: {
                    birthRate: 0.25,
                    deathRate: 0.02,
                    resourceRegen: 3.0,
                    energyConversion: 25,
                    resourceRequired: 0.8,
                    movementSpeed: 1.5,
                    energyDecay: 2
                }
            }
        };
    }

    function loadPreset(presetName) {
        if (!presetName || !parameterEditor.presets[presetName]) return;

        const preset = parameterEditor.presets[presetName];
        console.log(`📋 Cargando preset: ${preset.name}`);

        const newParameters = { ...parameterEditor.parameters, ...preset.parameters };

        updateParameterInputs(newParameters);

        parameterEditor.parameters = newParameters;
        parameterEditor.hasChanges = true;

        if (parameterEditor.autoApply) {
            applyParameters();
        } else {
            updateApplyButton();
        }

        showNotification(`Preset "${preset.name}" cargado`, 'success');

        document.getElementById('presetSelector').value = '';
    }

    function resetToDefaults() {
        if (confirm('¿Estás seguro de que quieres restablecer todos los parámetros a sus valores por defecto?')) {
            loadDefaultParameters();
            parameterEditor.hasChanges = true;

            if (parameterEditor.autoApply) {
                applyParameters();
            } else {
                updateApplyButton();
            }

            showNotification('Parámetros restablecidos a valores por defecto', 'info');
            console.log('🔄 Parámetros restablecidos');
        }
    }

    function savePreset() {
        const presetName = prompt('Nombre del preset personalizado:');
        if (!presetName) return;

        const customPreset = {
            name: `⚙️ ${presetName}`,
            description: 'Preset personalizado',
            parameters: { ...parameterEditor.parameters }
        };

        const savedPresets = JSON.parse(localStorage.getItem('simulationPresets') || '{}');
        savedPresets[presetName.toLowerCase().replace(/\s+/g, '_')] = customPreset;
        localStorage.setItem('simulationPresets', JSON.stringify(savedPresets));

        const presetSelector = document.getElementById('presetSelector');
        if (presetSelector) {
            const option = document.createElement('option');
            option.value = presetName.toLowerCase().replace(/\s+/g, '_');
            option.textContent = `⚙️ ${presetName}`;
            presetSelector.appendChild(option);
        }

        showNotification(`Preset "${presetName}" guardado`, 'success');
        console.log(`💾 Preset guardado: ${presetName}`);
    }

    function loadSavedPresets() {
        const savedPresets = JSON.parse(localStorage.getItem('simulationPresets') || '{}');
        const presetSelector = document.getElementById('presetSelector');

        if (!presetSelector) return;

        Object.entries(savedPresets).forEach(([key, preset]) => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = preset.name;
            presetSelector.appendChild(option);
        });

        parameterEditor.presets = { ...parameterEditor.presets, ...savedPresets };
    }

    function setupParameterWebSocketEvents() {
        if (!socket) return;

        socket.on('parameters_updated', (data) => {
            console.log('✅ Parámetros aplicados exitosamente:', data);
            updateParameterStatus('success', 'Parámetros aplicados exitosamente');

            setTimeout(() => {
                updateParameterStatus('ready', 'Listo para aplicar cambios');
            }, 2000);
        });

        socket.on('parameters_error', (data) => {
            console.error('❌ Error aplicando parámetros:', data);
            updateParameterStatus('error', `Error: ${data.error}`);
            showNotification(`Error aplicando parámetros: ${data.error}`, 'error');

            setTimeout(() => {
                updateParameterStatus('ready', 'Listo para aplicar cambios');
            }, 3000);
        });

        socket.on('current_parameters', (data) => {
            console.log('📥 Parámetros actuales recibidos:', data);

            if (data.parameters) {
                parameterEditor.parameters = { ...data.parameters };
                updateParameterInputs(data.parameters);
            }
        });
    }

    function requestCurrentParameters() {
        if (socket && socket.connected) {
            socket.emit('get_current_parameters');
        }
    }

    function initializeParameterEditorIntegration() {
        initializeParameterEditor();
        setupParameterWebSocketEvents();
        loadSavedPresets();

        if (socket && socket.connected) {
            requestCurrentParameters();
        }
    }

    // Integrar con la función init() principal
    const originalInit = init;
    init = function () {
        originalInit();
        setTimeout(initializeParameterEditorIntegration, 500);
    };

    // Exportar funciones para uso global
    window.SimulationController = {
        start: startSimulation,
        pause: pauseSimulation,
        reset: resetSimulation,
        step: stepSimulation,
        getState: () => simulationData,
        isRunning: () => simulationRunning,
        setSpeed: (speed) => {
            currentSpeed = speed;
            updateSpeedDisplay();
            if (socket) socket.emit('update_speed', { speed: speed });
        },
        getSpeed: () => currentSpeed,
        setMaxSteps: setMaxSteps,
        getMaxSteps: () => maxSteps,
        toggleAutoStop: toggleAutoStop,
        isAutoStop: () => autoStop,
        getHistory: () => ({
            population: [],
            resources: []
        }),
        exportChartData: exportChartData,
        showTrendAnalysis: showTrendAnalysis,
        resetCharts: resetChartsOnSimulationReset
    };

    window.ParameterEditor = {
        toggle: toggleParameterPanel,
        showTab: showTab,
        apply: applyParameters,
        reset: resetToDefaults,
        loadPreset: loadPreset,
        savePreset: savePreset,
        getParameters: () => ({ ...parameterEditor.parameters }),
        setParameter: (key, value) => {
            parameterEditor.parameters[key] = value;
            const slider = document.getElementById(key);
            const numberInput = document.getElementById(key + 'Num');
            if (slider) slider.value = value;
            if (numberInput) numberInput.value = value;
        }
    };

    // Hacer funciones globales para el template HTML
    window.applyConfigurationViaSocket = applyConfigurationViaSocket;
    window.toggleParameterPanel = toggleParameterPanel;
    window.showTab = showTab;
    window.applyParameters = applyParameters;
    window.resetToDefaults = resetToDefaults;
    window.loadPreset = loadPreset;
    window.savePreset = savePreset;
    window.socket = socket; // Hacer socket global para el HTML

    // NUEVA FUNCIÓN GLOBAL: Aplicar tamaño de rejilla
    window.applyGridSize = function() {
        const width = parseInt(document.getElementById('gridWidth')?.value || 50);
        const height = parseInt(document.getElementById('gridHeight')?.value || 50);
        
        if (width < 10 || width > 200 || height < 10 || height > 200) {
            showNotification('Las dimensiones deben estar entre 10 y 200', 'error');
            return;
        }
        
        if (!socket || !socket.connected) {
            showNotification('No hay conexión con el servidor', 'error');
            return;
        }
        
        const button = document.getElementById('applyGridBtn');
        if (button) {
            button.disabled = true;
            button.textContent = '⏳ Aplicando...';
        }
        
        socket.emit('update_grid_size', {
            gridWidth: width,
            gridHeight: height
        });
        
        console.log(`📐 Solicitando cambio de rejilla a ${width}x${height}`);
    };

    window.exportCurrentData = function () {
        if (window.SimulationController && window.SimulationController.getState()) {
            const data = {
                state: window.SimulationController.getState(),
                history: {
                    population: simulationData.last_populations || [],
                    resources: simulationData.system_metrics?.total_resources_history || []
                },
                timestamp: new Date().toISOString(),
                config: {
                    mode: document.getElementById('simulation_mode')?.value,
                    config_file: document.getElementById('config_file')?.value,
                    seed: document.getElementById('seed')?.value
                }
            };

            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `simulation_data_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showNotification('Datos exportados con éxito!', 'success');
        } else {
            showNotification('No hay datos de simulación disponibles para exportar.', 'error');
        }
    }

    console.log('✅ Simulación completamente configurada con formas de especies y parámetros de rejilla');
});

function updateMaxSteps() {
    const input = document.getElementById('maxStepsInput');
    if (input && window.SimulationController) {
        const newMaxSteps = parseInt(input.value);
        if (newMaxSteps >= 50 && newMaxSteps <= 2000) {
            window.SimulationController.setMaxSteps(newMaxSteps);
            console.log(`📊 Máximo de pasos establecido en ${newMaxSteps}`);
        } else {
            console.warn('⚠️ El máximo de pasos debe estar entre 50 y 2000');
        }
    }
}