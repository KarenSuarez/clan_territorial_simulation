// simulation.js - Versión completa corregida con estado dinámico
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
    
    // Elementos de control
    const speedSlider = document.getElementById('speedSlider');
    const speedValue = document.getElementById('speedValue');
    const autoResetCheckbox = document.getElementById('autoReset');
    
    // Estado de la simulación
    let simulationData = null;
    let simulationRunning = false;
    let cellSize = 12;
    let socket = null;
    let currentSpeed = 1.0;
    let maxSteps = 500;
    let autoStop = true;
    
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
        updateCanvasSize();
        updateButtonStates();
        updateStatusIndicator(false); // Inicializar como detenido
        startStatusMonitoring();
        
        console.log('✅ Simulación inicializada');
    }
    
    function setupSocket() {
        console.log('🔌 Configurando WebSocket...');
        
        try {
            socket = io.connect();
            
            socket.on('connect', () => {
                console.log('✅ WebSocket conectado');
                updateConnectionStatus(true);
                // Solicitar estado inicial al conectar
                socket.emit('request_state');
            });
            
            socket.on('disconnect', () => {
                console.log('❌ WebSocket desconectado');
                updateConnectionStatus(false);
                simulationRunning = false;
                updateStatusIndicator(false);
                updateButtonStates();
            });
            
            socket.on('simulation_state', (data) => {
                console.log('📥 Estado recibido:', data);
                console.log(`📊 Datos: paso=${data.step}, clanes=${data.clans ? data.clans.length : 0}, running=${data.running}`);
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
                updateControlsDisplay();
            });
            
            // Solicitar configuración inicial
            socket.emit('get_speed');
            socket.emit('get_simulation_config');
            
        } catch (error) {
            console.error('❌ Error configurando WebSocket:', error);
        }
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
        
        // Control de velocidad
        if (speedSlider) {
            speedSlider.addEventListener('input', () => {
                console.log('🎚️ Slider de velocidad cambiado:', speedSlider.value);
                updateSimulationSpeed();
            });
        }
        
        // Auto-reset checkbox
        if (autoResetCheckbox) {
            autoResetCheckbox.addEventListener('change', () => {
                console.log('🔄 Auto-reset toggled:', autoResetCheckbox.checked);
                toggleAutoStop();
            });
        }
        
        // Atajos de teclado
        document.addEventListener('keydown', (event) => {
            if (event.target.tagName === 'INPUT') return;
            
            switch(event.key) {
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
        console.log(`📊 Procesando estado: ${data.clans ? data.clans.length : 0} clanes, paso ${data.step}`);
        
        simulationData = data;
        
        // Actualizar estado de ejecución basado en datos del servidor
        simulationRunning = data.running || false;
        updateStatusIndicator(simulationRunning);
        updateButtonStates();
        
        renderSimulation();
        updateMetrics();
        updateClanMetrics();
        updateProgressIndicator();
    }
    
    function updateStatusIndicator(isRunning) {
        console.log(`🔄 Actualizando estado visual: ${isRunning ? 'Ejecutando' : 'Detenido'}`);
        
        // Actualizar el indicador visual (círculo de color)
        if (statusIndicator) {
            statusIndicator.className = `status-indicator ${isRunning ? 'status-running' : 'status-stopped'}`;
        }
        
        // Actualizar el texto del estado
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
        
        // Actualizar estado inmediatamente (se confirmará con el evento del servidor)
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
                // Solicitar estado actual cada 3 segundos para mantener sincronización
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
        
        // Convertir valor del slider (1-200) a multiplicador de velocidad (0.1x - 5.0x)
        const sliderValue = parseInt(speedSlider.value);
        let speedMultiplier;
        
        if (sliderValue <= 100) {
            // 1-100 -> 0.1x-1.0x (más lento a normal)
            speedMultiplier = (sliderValue / 100) * 0.9 + 0.1;
        } else {
            // 101-200 -> 1.0x-5.0x (normal a muy rápido)
            speedMultiplier = 1.0 + ((sliderValue - 100) / 100) * 4.0;
        }
        
        console.log(`🎚️ Actualizando velocidad: slider=${sliderValue}, speed=${speedMultiplier.toFixed(1)}x`);
        
        // Enviar al servidor
        socket.emit('update_speed', { speed: speedMultiplier });
        
        // Actualizar display inmediatamente
        currentSpeed = speedMultiplier;
        updateSpeedDisplay();
    }
    
    function updateSpeedDisplay() {
        if (speedValue) {
            speedValue.textContent = `${currentSpeed.toFixed(1)}x`;
            
            // Actualizar color según velocidad
            if (currentSpeed < 0.5) {
                speedValue.style.color = '#e74c3c'; // Rojo para muy lento
            } else if (currentSpeed < 1.0) {
                speedValue.style.color = '#f39c12'; // Naranja para lento
            } else if (currentSpeed <= 1.5) {
                speedValue.style.color = '#27ae60'; // Verde para normal
            } else {
                speedValue.style.color = '#3498db'; // Azul para rápido
            }
        }
        
        // Sincronizar slider si es necesario
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
            // 0.1x-1.0x -> 1-100
            sliderValue = Math.round(((currentSpeed - 0.1) / 0.9) * 100);
        } else {
            // 1.0x-5.0x -> 100-200
            sliderValue = Math.round(100 + ((currentSpeed - 1.0) / 4.0) * 100);
        }
        
        speedSlider.value = Math.max(1, Math.min(200, sliderValue));
    }
    
    function updateProgressIndicator() {
        // Actualizar indicador de progreso si existe
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
        
        // Actualizar display de pasos máximos
        const maxStepsInput = document.getElementById('maxStepsInput');
        if (maxStepsInput) {
            maxStepsInput.value = maxSteps;
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
        
        // Limpiar canvas
        ctx.clearRect(0, 0, gridCanvas.width, gridCanvas.height);
        
        // Renderizar recursos
        renderResources(grid, rows, cols);
        
        // Renderizar clanes
        renderClans(clans);
        
        // Renderizar grid si las celdas son grandes
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
    
    function renderClans(clans) {
        clans.forEach((clan) => {
            const x = clan.position[0] * cellSize + cellSize / 2;
            const y = clan.position[1] * cellSize + cellSize / 2;
            const radius = Math.max(4, Math.min(cellSize / 2, clan.visual_size || Math.sqrt(clan.size) * 1.5));
            
            // Color basado en estado
            const color = stateColors[clan.state] || '#95a5a6';
            
            // Círculo del clan
            ctx.beginPath();
            ctx.arc(x, y, radius, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();
            
            // Borde
            ctx.strokeStyle = adjustColor(color, -30);
            ctx.lineWidth = 2;
            ctx.stroke();
            
            // Texto del tamaño
            if (cellSize > 10) {
                ctx.fillStyle = 'white';
                ctx.font = `bold ${Math.max(8, cellSize * 0.4)}px Arial`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(clan.size.toString(), x, y);
            }
            
            // Barra de energía
            if (cellSize > 12 && clan.energy !== undefined) {
                drawEnergyBar(x, y - radius - 6, radius * 1.8, clan.energy);
            }
        });
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
        ctx.fillRect(x - width/2, y, width, barHeight);
        
        // Barra de energía
        let color;
        if (energyPercent > 0.6) color = '#27ae60';
        else if (energyPercent > 0.3) color = '#f39c12';
        else color = '#e74c3c';
        
        ctx.fillStyle = color;
        ctx.fillRect(x - width/2, y, width * energyPercent, barHeight);
        
        // Borde
        ctx.strokeStyle = 'rgba(0,0,0,0.5)';
        ctx.lineWidth = 1;
        ctx.strokeRect(x - width/2, y, width, barHeight);
    }
    
    function updateMetrics() {
        if (!simulationData) return;
        
        const totalPop = simulationData.clans ? simulationData.clans.reduce((sum, clan) => sum + clan.size, 0) : 0;
        const totalRes = simulationData.resource_grid ? 
            simulationData.resource_grid.flat().reduce((sum, r) => sum + r, 0) : 0;
        
        if (populationDisplay) populationDisplay.textContent = totalPop;
        if (totalResourceDisplay) totalResourceDisplay.textContent = totalRes.toFixed(1);
        if (stepCountDisplay) stepCountDisplay.textContent = `${simulationData.step || 0}/${maxSteps}`;
        if (timeElapsedDisplay) timeElapsedDisplay.textContent = formatTime(simulationData.time || 0);
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
            const color = stateColors[clan.state] || '#95a5a6';
            const stateEmoji = getStateEmoji(clan.state);
            
            html += `
                <div class="clan-metric" style="border-left: 4px solid ${color}; margin-bottom: 0.5rem; padding: 0.8rem; background: white; border-radius: 4px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>🏛️ Clan ${clan.id}</strong>
                        <span>${stateEmoji} ${clan.state}</span>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.3rem; font-size: 0.9rem; margin-top: 0.5rem;">
                        <span>👥 Tamaño: <strong>${clan.size}</strong></span>
                        <span>⚡ Energía: <strong>${clan.energy?.toFixed(1)}%</strong></span>
                        <span>📍 X: <strong>${clan.position[0].toFixed(1)}</strong></span>
                        <span>📍 Y: <strong>${clan.position[1].toFixed(1)}</strong></span>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
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
        // Implementar si tienes un indicador de conexión
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
        // Función simple para ajustar brillo del color
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
        
        // Crear elemento de notificación
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
        
        // Colores según tipo
        const colors = {
            success: '#27ae60',
            error: '#e74c3c',
            warning: '#f39c12',
            info: '#3498db'
        };
        notification.style.backgroundColor = colors[type] || colors.info;
        
        document.body.appendChild(notification);
        
        // Animar entrada
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Animar salida y remover
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
    
    // Exportar funciones para acceso externo
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
        }) // Placeholder para compatibilidad
    };
    
    console.log('✅ Simulación completamente configurada con estado dinámico');
});

// Función global para actualizar máximo de pasos (llamada desde HTML)
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