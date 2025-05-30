# clan_territorial_simulation/docs/user_manual.md
# # Manual de Usuario de la Simulación Territorial de Clanes

# ## 1. Introducción

# Este manual proporciona una guía para utilizar la interfaz web de la Simulación Territorial de Clanes. La simulación permite modelar la competencia y la dinámica de poblaciones de clanes en un entorno de recursos.

# ## 2. Requisitos del Sistema

# - Navegador web moderno (Chrome, Firefox, Safari, Edge).
# - Conexión a internet (para acceder a la interfaz).

# ## 3. Instalación (para desarrolladores)

# Si deseas ejecutar la simulación localmente (para desarrollo o pruebas avanzadas), sigue estos pasos:

# 1. **Clonar el repositorio:**
#    ```bash
#    git clone [https://github.com/sindresorhus/del](https://github.com/sindresorhus/del)
#    cd clan_territorial_simulation
#    ```

# 2. **Crear un entorno virtual (recomendado):**
#    ```bash
#    python -m venv venv
#    source venv/bin/activate  # En Linux/macOS
#    venv\Scripts\activate  # En Windows
#    ```

# 3. **Instalar las dependencias:**
#    ```bash
#    pip install -r requirements.txt
#    ```

# 4. **Ejecutar la aplicación Flask:**
#    ```bash
#    python app.py
#    ```

# 5. **Abrir en el navegador:** Accede a `http://127.0.0.1:5000/` en tu navegador web.

# ## 4. Interfaz Web

# ### 4.1 Página de Inicio

# - **Título:** Muestra el nombre de la simulación.
# - **Navegación:** Barra de menú con enlaces a las diferentes secciones:
#    - **Inicio:** Te lleva de vuelta a esta página.
#    - **Simulación:** Permite configurar y controlar la simulación.
#    - **Análisis Científico:** Muestra gráficos y resultados de análisis.

# ### 4.2 Página de Simulación

# - **Configuración de la Simulación:**
#    - **Modo de Simulación:** Selecciona entre diferentes modos (e.g., estocástico, determinista).
#    - **Archivo de Configuración:** Elige un archivo `.json` predefinido para cargar parámetros iniciales (tamaño de la rejilla, número de clanes, etc.). Hay configuraciones de ejemplo disponibles.
#    - **Semilla (Opcional):** Introduce un valor entero para la semilla aleatoria si deseas resultados reproducibles en modo estocástico.
#    - **Botón "Iniciar Simulación":** Comienza la simulación con la configuración seleccionada.

# - **Control de la Simulación:**
#    - **Botón "Iniciar":** Reanuda o inicia la simulación.
#    - **Botón "Pausar":** Detiene la simulación en el estado actual.
#    - **Botón "Paso":** Ejecuta un solo paso de la simulación.
#    - **Botón "Resetear":** Detiene la simulación y la reinicia con la configuración actual.

# - **Visualización de la Simulación:**
#    - Un lienzo que muestra la rejilla. Los recursos pueden estar representados por la intensidad del color, y los clanes por círculos de diferentes colores y tamaños (relativos a su población).
#    - Información en tiempo real sobre el estado de la simulación (tiempo transcurrido, número de clanes, etc.).

# ### 4.3 Página de Análisis Científico

# - Esta página muestra diferentes gráficos y resultados de análisis generados a partir de los datos de la simulación:
#    - **Gráficos Temporales:** Población de cada clan a lo largo del tiempo.
#    - **Mapas de Calor:** Densidad territorial de los clanes en la rejilla.
#    - **Patrones Espaciales:** Análisis de la distribución espacial de los clanes (e.g., distancia promedio).
#    - **Métricas de Convergencia:** Resultados del análisis de convergencia numérica.
#    - **Estadísticas de Clanes:** Tamaño promedio, máximo y mínimo de cada clan.
#    - **Correlación de Variables:** Matriz de correlación entre variables como tamaño del clan y recursos locales.
#    - **Distribución de Probabilidad:** Distribución del tamaño de la población total.

# - **Exportar Datos y Reportes:**
#    - **Botones para exportar:**
#        - Datos de la simulación en formato CSV.
#        - Datos de la simulación en formato JSON.
#        - Un reporte científico completo en formato HTML (incluye gráficos).
#        - (Funcionalidad para exportar gráficos individuales podría estar disponible).
#        - Generar una animación de la simulación en formato HTML.

# ### 4.4 Página de Reporte de Análisis

# - Muestra reportes de análisis específicos, como el de conservación, convergencia o sensibilidad, en formato de texto.

# ### 4.5 Página de Animación

# - Muestra una animación de la evolución de la simulación a lo largo del tiempo.

# ## 5. Casos de Uso

# - **Explorar la dinámica de la competencia territorial:** Observa cómo los clanes interactúan y compiten por los recursos.
# - **Analizar el impacto de diferentes parámetros:** Modifica las tasas de natalidad, mortalidad, movimiento, etc., para ver cómo afectan la simulación.
# - **Validar el modelo:** Utiliza las herramientas de análisis para verificar la conservación, convergencia y sensibilidad del modelo.
# - **Generar reportes científicos:** Documenta tus hallazgos exportando datos y reportes.
# - **Crear visualizaciones:** Presenta los resultados de la simulación de manera clara y efectiva.

# ## 6. Solución de Problemas

# - **La simulación no se inicia:** Verifica que hayas seleccionado un modo de simulación y, opcionalmente, un archivo de configuración válido.
# - **Los gráficos no se muestran:** Asegúrate de que tu navegador web soporta JavaScript y que no hay errores en la consola del navegador.
# - **Errores durante el análisis o la exportación:** Revisa la consola del servidor (donde se ejecuta `app.py`) para ver si hay mensajes de error.
# - **Rendimiento lento:** Para simulaciones grandes, considera reducir el tamaño de la rejilla o el número de clanes. Las optimizaciones de rendimiento están en curso.

# ## 7. Contacto

# Si tienes preguntas o encuentras problemas, por favor contacta a [tu dirección de correo electrónico o enlace al repositorio].