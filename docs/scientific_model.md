# clan_territorial_simulation/docs/scientific_model.md
# # Documentación del Modelo Matemático de la Simulación Territorial de Clanes

# ## 1. Introducción

# Este documento describe el modelo matemático subyacente a la simulación de competencia territorial entre clanes. El modelo se basa en la interacción de poblaciones de clanes con un entorno de recursos limitado y la dinámica de sus territorios.

# ## 2. Entorno

# ### 2.1 Rejilla Espacial

# El entorno se representa como una rejilla bidimensional discreta de tamaño $L_x \times L_y$. La topología de la rejilla es toroidal, lo que significa que los bordes se conectan (un objeto que sale por un borde reaparece por el opuesto).

# ### 2.2 Recursos

# Cada celda $(x, y)$ de la rejilla contiene una cantidad de recurso $R(x, y, t)$ en el tiempo $t$. La dinámica de los recursos se describe por la siguiente ecuación:

# $$
# \frac{dR(x, y, t)}{dt} = \alpha R_{max} \left(1 - \frac{R(x, y, t)}{R_{max}}\right) - \sum_{i \in \text{clanes}} C_i(x, y, t)
# $$

# donde:
# - $\alpha$ es la tasa de regeneración del recurso.
# - $R_{max}$ es la capacidad de carga máxima del recurso por celda.
# - $C_i(x, y, t)$ es la tasa de consumo del recurso por el clan $i$ en la celda $(x, y)$ en el tiempo $t$.

# ### 2.3 Gradiente de Recursos

# Los clanes pueden percibir el gradiente de recursos $\nabla R(x, y, t)$, que se calcula como:

# $$
# \nabla R(x, y, t) = \left( \frac{\partial R}{\partial x}, \frac{\partial R}{\partial y} \right)
# $$

# En la implementación discreta, esto se aproxima utilizando diferencias finitas.

# ## 3. Clanes

# ### 3.1 Población

# Cada clan $i$ tiene un tamaño de población $N_i(t)$. La dinámica de la población se describe por:

# $$
# \frac{dN_i(t)}{dt} = (\beta_i - \mu_{i,n} - \mu_{i,c}(t) - \mu_{i,s}(t)) N_i(t)
# $$

# donde:
# - $\beta_i$ es la tasa de natalidad del clan $i$.
# - $\mu_{i,n}$ es la tasa de mortalidad natural del clan $i$.
# - $\mu_{i,c}(t)$ es la tasa de mortalidad por competencia (dependiente de la densidad de clanes en el territorio).
# - $\mu_{i,s}(t)$ es la tasa de mortalidad por inanición, que depende de la disponibilidad de recursos.

# La tasa de mortalidad por inanición $\mu_{i,s}(t)$ se modela como:

# $$
# \mu_{i,s}(t) = \mu_{s,max} e^{-R_{local}(i, t) / R_{req}}
# $$

# donde $R_{local}(i, t)$ es la cantidad de recurso disponible para el clan $i$ y $R_{req}$ es el recurso requerido por individuo.

# ### 3.2 Movimiento

# La posición del centro del clan $i$ es $\mathbf{p}_i(t) = (x_i(t), y_i(t))$. El movimiento se describe por:

# $$
# \frac{d\mathbf{p}_i(t)}{dt} = v_i \nabla R(\mathbf{p}_i(t), t) + \sigma_i \boldsymbol{\epsilon}(t)
# $$

# donde:
# - $v_i$ es la velocidad de movimiento del clan $i$.
# - $\sigma_i$ es la intensidad del movimiento aleatorio.
# - $\boldsymbol{\epsilon}(t)$ es un vector de ruido aleatorio.

# ### 3.3 Consumo de Recursos

# La tasa de consumo de recursos del clan $i$ en una celda $(x, y)$ depende de su tamaño y de la disponibilidad local:

# $$
# C_i(x, y, t) = N_i(t) \cdot f(dist(\mathbf{p}_i(t), (x, y))) \cdot \rho(R(x, y, t)) \cdot \eta_i
# $$

# donde:
# - $f$ es una función de distribución espacial del consumo alrededor del centro del clan.
# - $\rho$ es una función de la tasa de consumo dependiente de la disponibilidad del recurso.
# - $\eta_i$ es la eficiencia de forrajeo del clan $i$.

# ### 3.4 Competencia

# La mortalidad por competencia $\mu_{i,c}(t)$ puede depender de la superposición de los territorios de los clanes y la densidad de población en esas áreas.

# ## 4. Reproducción y Muerte

# La reproducción ocurre probabilísticamente basada en la tasa de natalidad $\beta_i$. La muerte ocurre por causas naturales (tasa $\mu_{i,n}$), competencia ($\mu_{i,c}$), e inanición ($\mu_{i,s}$).

# ## 5. Patrones Emergentes

# El modelo está diseñado para simular la emergencia de patrones como fronteras territoriales estables, migraciones, y especialización territorial a través de las interacciones locales de los clanes y el entorno.

# ## 6. Análisis y Validación

# La validación del modelo se realiza mediante la verificación de leyes de conservación (población total, recursos), análisis de convergencia numérica (variando el paso de tiempo $dt$), análisis de sensibilidad a las condiciones iniciales (usando métodos de Monte Carlo), y la comparación con resultados teóricos o datos empíricos si están disponibles.

# ## 7. Extensiones Futuras

# Las extensiones futuras del modelo podrían incluir la introducción de interacciones sociales más complejas dentro de los clanes, la diferenciación de especies o tipos de clanes, y la incorporación de cambios ambientales dinámicos.