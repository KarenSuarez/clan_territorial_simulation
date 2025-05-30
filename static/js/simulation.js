// clan_territorial_simulation/static/js/simulation.js
document.addEventListener('DOMContentLoaded', () => {
    const gridCanvas = document.getElementById('gridCanvas');
    const ctx = gridCanvas.getContext('2d');
    const playButton = document.getElementById('playButton');
    const pauseButton = document.getElementById('pauseButton');
    const resetButton = document.getElementById('resetButton');
    const stepButton = document.getElementById('stepButton');
    const populationDisplay = document.getElementById('population');
    const totalResourceDisplay = document.getElementById('totalResource');
    const modeDisplay = document.getElementById('modeDisplay');
    const speedSlider = document.getElementById('speedSlider');
    const speedValue = document.getElementById('speedValue');

    let simulationRunning = false;
    let simulationData = null;
    let cellSize;
    let updateInterval = 100; // ms

    const socket = io.connect(window.location.protocol + '//' + document.domain + ':' + location.port);

    socket.on('connect', () => {
        console.log('WebSocket connected');
        socket.emit('request_state'); // Request initial state
    });

    socket.on('simulation_state', (data) => {
        simulationData = data;
        renderSimulation();
        updateMetrics();
        if (simulationRunning) {
            setTimeout(() => {
                socket.emit('step_simulation');
            }, updateInterval);
        }
    });

    function updateCanvasSize() {
        if (simulationData && simulationData.resource_grid && simulationData.resource_grid.length > 0) {
            const rows = simulationData.resource_grid.length;
            const cols = simulationData.resource_grid[0].length;
            cellSize = Math.min(gridCanvas.clientWidth / cols, gridCanvas.clientHeight / rows);
            gridCanvas.width = cols * cellSize;
            gridCanvas.height = rows * cellSize;
        }
    }

    function renderSimulation() {
        if (!simulationData || !simulationData.resource_grid) return;

        updateCanvasSize();
        const grid = simulationData.resource_grid;
        const clans = simulationData.clans;
        const rows = grid.length;
        const cols = grid[0].length;

        // Render resources
        for (let y = 0; y < rows; y++) {
            for (let x = 0; x < cols; x++) {
                const resourceLevel = grid[y][x];
                const intensity = Math.min(1, resourceLevel / 100); // Normalize for color intensity
                const color = `rgba(0, 100, 0, ${intensity})`; // Green for resources
                ctx.fillStyle = color;
                ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
            }
        }

        // Render clans
        clans.forEach(clan => {
            const x = clan.position[0] * cellSize + cellSize / 2;
            const y = clan.position[1] * cellSize + cellSize / 2;
            const radius = Math.sqrt(clan.size) * 1.5; // Size affects radius
            ctx.beginPath();
            ctx.arc(x, y, radius, 0, 2 * Math.PI);
            ctx.fillStyle = getRandomColor(clan.id); // Different color per clan
            ctx.fill();
            ctx.closePath();
        });
    }

    function getRandomColor(id) {
        const hue = id * 30; // Spread colors
        return `hsl(${hue}, 70%, 50%)`;
    }

    function updateMetrics() {
        if (!simulationData) return;
        const totalPopulation = simulationData.clans.reduce((sum, clan) => sum + clan.size, 0);
        const totalResource = simulationData.resource_grid.flat().reduce((sum, r) => sum + r, 0);
        populationDisplay.textContent = `Población Total: ${totalPopulation}`;
        totalResourceDisplay.textContent = `Recursos Totales: ${totalResource.toFixed(2)}`;
        if (simulationData.mode) {
            modeDisplay.textContent = `Modo: ${simulationData.mode}`;
        } else if (document.getElementById('simulation_mode')) {
            modeDisplay.textContent = `Modo: ${document.getElementById('simulation_mode').value}`;
        }
    }

    playButton.addEventListener('click', () => {
        simulationRunning = true;
        socket.emit('start_simulation');
    });

    pauseButton.addEventListener('click', () => {
        simulationRunning = false;
        socket.emit('pause_simulation');
    });

    resetButton.addEventListener('click', () => {
        simulationRunning = false;
        socket.emit('reset_simulation');
    });

    stepButton.addEventListener('click', () => {
        socket.emit('step_simulation');
    });

    speedSlider.addEventListener('input', () => {
        updateInterval = 200 - parseInt(speedSlider.value);
        speedValue.textContent = `${(1000 / updateInterval).toFixed(1)}x`;
    });

    window.addEventListener('resize', updateCanvasSize);
});