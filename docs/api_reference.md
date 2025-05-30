# clan_territorial_simulation/docs/api_reference.md
# # Referencia de la API de la Simulación Territorial de Clanes

# ## 1. Introducción

# Esta documentación describe las principales funciones y rutas de la API de la Simulación Territorial de Clanes. Está orientada a desarrolladores que deseen interactuar con la simulación a un nivel más bajo o integrar sus funcionalidades en otras aplicaciones.

# ## 2. Rutas de la API (Flask)

# ### 2.1 `/` (GET)

# - **Descripción:** Página de inicio de la aplicación web.
# - **Retorna:** Renderiza la plantilla `index.html`.

# ### 2.2 `/simulation` (GET)

# - **Descripción:** Muestra la página de configuración y control de la simulación.
# - **Retorna:** Renderiza la plantilla `simulation.html`.

# ### 2.3 `/simulation` (POST)

# - **Descripción:** Inicializa la simulación con los parámetros enviados a través del formulario.
# - **Parámetros (en el cuerpo de la solicitud):**
#    - `simulation_mode` (string, requerido): El modo de sim
#    - `config_file` (string, opcional): Nombre del archivo de configuración (sin extensión `.json`) en la carpeta `data/configs/`.
#    - `seed` (integer, opcional): Semilla aleatoria para la simulación.
# - **Retorna:** Redirige a la página `/simulation`.

# ### 2.4 `/analysis` (GET)

# - **Descripción:** Muestra la página de análisis científico con gráficos y estadísticas.
# - **Retorna:** Renderiza la plantilla `analysis.html`, pasando los datos de los gráficos y análisis.

# ### 2.5 `/analysis/conservation` (GET)

# - **Descripción:** Realiza el análisis de conservación y muestra el reporte.
# - **Retorna:** Renderiza la plantilla `analysis_report.html` con el reporte de conservación.

# ### 2.6 `/analysis/convergence` (GET)

# - **Descripción:** Realiza el análisis de convergencia temporal y muestra el reporte.
# - **Retorna:** Renderiza la plantilla `analysis_report.html` con el reporte de convergencia.

# ### 2.7 `/analysis/sensitivity` (GET)

# - **Descripción:** Realiza el análisis de sensibilidad de Monte Carlo y muestra el reporte.
# - **Retorna:** Renderiza la plantilla `analysis_report.html` con el reporte de sensibilidad.

# ### 2.8 `/export/<format>` (GET)

# - **Descripción:** Exporta los datos de la simulación en el formato especificado.
# - **Parámetros (en la URL):**
#    - `format` (string, requerido): El formato de exportación (`csv` o `json`).
# - **Retorna:** Un mensaje indicando el estado de la exportación.

# ### 2.9 `/report` (GET)

# - **Descripción:** Genera un reporte científico completo en formato HTML.
# - **Retorna:** Un mensaje indicando el estado de la generación del reporte. El archivo se guarda en `data/exports/report.html`.

# ### 2.10 `/animation` (GET)

# - **Descripción:** Genera una página HTML con una animación de la simulación.
# - **Retorna:** Renderiza la plantilla `animation.html`, pasando los datos de la simulación.

# ## 3. Eventos de SocketIO

# ### 3.1 `connect`

# - **Descripción:** Evento emitido por el cliente cuando se conecta al servidor WebSocket.
# - **Emite al cliente:** El estado actual de la simulación (`simulation_state`).

# ### 3.2 `disconnect`

# - **Descripción:** Evento emitido por el cliente cuando se desconecta del servidor WebSocket.

# ### 3.3 `start_simulation` (Emitted by client)

# - **Descripción:** Solicita al servidor que inicie o reanude la simulación.

# ### 3.4 `pause_simulation` (Emitted by client)

# - **Descripción:** Solicita al servidor que pause la simulación.

# ### 3.5 `reset_simulation` (Emitted by client)

# - **Descripción:** Solicita al servidor que detenga y reinicie la simulación.

# ### 3.6 `step_simulation` (Emitted by client)

# - **Descripción:** Solicita al servidor que ejecute un solo paso de la simulación.

# ### 3.7 `request_state` (Emitted by client)

# - **Descripción:** Solicita al servidor el estado actual de la simulación.
# - **Emite al cliente:** El estado actual de la simulación (`simulation_state`).

# ### 3.8 `simulation_state` (Emitted by server)

# - **Descripción:** Envía el estado actual de la simulación al cliente para su visualización.
# - **Datos enviados (JSON):**
#    - `time`: Tiempo actual de la simulación.
#    - `clans`: Lista de diccionarios, cada uno representando un clan con su `id`, `size`, `position`, etc.
#    - `resource_grid`: Rejilla de recursos actual.
#    - `mode`: El modo de simulación actual.

# ## 4. Estructura de Datos (JSON)

# ### 4.1 Estado de la Simulación

# ```json
# {
#   "time": 10.5,
#   "clans": [
#     {
#       "id": 1,
#       "size": 25,
#       "position": [50, 75],
#       "velocity": [0.1, -0.2],
#       "sigma": 0.05,
#       "parameters": {
#         "birth_rate": 0.1,
#         "natural_death_rate": 0.02,
#         "resource_required_per_individual": 0.1
#       }
#     },
#     // ... más clanes
#   ],
#   "resource_grid": [
#     [85.2, 90.1, ...],
#     [78.9, 82.5, ...],
#     // ... la rejilla de recursos
#   ]
# }
# ```

# ### 4.2 Archivo de Configuración (`.json`)

# ```json
# {
#   "grid_size": [100, 100],
#   "initial_clan_count": 10,
#   "min_clan_size": 5,
#   "max_clan_size": 20,
#   "resource_max": 100.0,
#   "resource_regeneration_rate": 0.05,
#   "initial_clan_parameters": {
#     "birth_rate": [0.08, 0.12],
#     "natural_death_rate": [0.01, 0.03],
#     "velocity": [0.05, 0.15],
#     "sigma": [0.02, 0.08]
#   },
#   "environment_parameters": {
#     "initial_resource_distribution": "uniform"
#   }
#   // ... otros parámetros
# }
# ```

# ## 5. Manejo de Errores

# La API utiliza códigos de estado HTTP estándar para indicar el éxito o el fallo de las solicitudes. Los errores específicos de la simulación pueden devolverse en el cuerpo de la respuesta como objetos JSON con un mensaje descriptivo. El servidor también registra los errores utilizando el sistema de logging implementado.

# ## 6. Extensiones Futuras

# - Implementación de autenticación y autorización para proteger las funcionalidades de la API.
# - Adición de endpoints para manipular parámetros de la simulación en tiempo real.
# - Soporte para diferentes formatos de salida (e.g., XML).