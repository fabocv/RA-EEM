# RA-EEM — Resumen Matemático-Teórico
## Relational Allostatic Emergent Energy Model · v0.3.4

---

## 1. Descripción General

RA-EEM es un modelo de simulación de díadas emocionales. Representa la interacción entre dos agentes —**Sujeto (i)** y **Alter (j)**— como un sistema dinámico acoplado, estocástico y con retardo temporal.

El modelo no busca reproducir el comportamiento de personas reales, sino explorar **patrones emergentes** que surgen de distintas configuraciones psicológicas. La conducta observable es una función de múltiples estados internos interactuando bajo incertidumbre.

Cada agente posee los siguientes **estados internos**:

| Variable | Rango | Descripción |
|----------|-------|-------------|
| `H` | `[-1, 1]` | Emisión conductual observable |
| `I` | `[0, 1]` | Angustia acumulada |
| `C` | `[0, 1]` | Burnout relacional (carga alostática) |
| `M` | `[-1, 1]` | Memoria relacional subjetiva |
| `E` | `[-1, 1]` | Expectativas internas sobre el otro |
| `w̃_a` | `[0, 1]` | Activación ansiosa dinámica |
| `w̃_e` | `[0, 1]` | Activación evitativa dinámica |

Y los siguientes **rasgos fijos** (parámetros del agente):

| Parámetro | Descripción |
|-----------|-------------|
| `w_s` | Seguridad basal |
| `w_a` | Ansiedad de apego basal |
| `w_e` | Evitación basal |
| `w_d` | Desorganización |
| `G` | Empatía / responsividad |
| `A` | Agencia relacional |
| `P` | Rigidez predictiva (0 = flexible, 1 = rígido) |
| `R` | Reserva de recursos ejecutivos |

---

## 2. Retardo Temporal

Antes de cualquier cómputo, cada agente opera sobre **la conducta del otro con un retardo de `τ` pasos**:

$$H_i^{(\tau)}[t] = H_i[t - \tau], \quad H_j^{(\tau)}[t] = H_j[t - \tau]$$

> **Justificación:** Las personas no responden instantáneamente al otro. El procesamiento emocional tarda —especialmente en estilos de apego ansioso o en relaciones con alta carga cognitiva. `τ` modela este delay de integración: a mayor `τ`, más lento el sistema actualiza su percepción.

---

## 3. Error Predictivo

Cada agente calcula cuánto difiere la conducta percibida del otro de lo que esperaba:

$$\varepsilon_i[t] = H_j^{(\tau)}[t] - E_i[t]$$

$$\varepsilon_j[t] = H_i^{(\tau)}[t] - E_j[t]$$

El error efectivo amplifica o atenúa según la rigidez predictiva del agente:

$$\varepsilon_i^{\text{eff}} = P_i \cdot \varepsilon_i$$

> **Justificación:** El procesamiento predictivo (Friston, Clark) postula que el cerebro genera expectativas sobre el mundo social y procesa la diferencia entre predicción y realidad. Un agente con `P` alto (rígido) amplifica los errores porque no los neutraliza con actualización flexible de sus modelos internos. Modela la "predictive rigidity" observada en apego inseguro crónico.

---

## 4. Filtro Perceptivo

La conducta del otro no se percibe tal cual, sino filtrada por el historial relacional (`M`) y el sesgo del error predictivo:

$$\hat{H}_{j \to i}[t] = \begin{cases}
H_j^{(\tau)} \cdot \left(1 + \kappa \cdot \max(0, \varepsilon_i^{\text{eff}}) \cdot |M_i|\right) & \text{si } \varepsilon_i^{\text{eff}} \geq 0 \\
H_j^{(\tau)} \cdot \left(1 + \chi \cdot \max(0, -\varepsilon_i^{\text{eff}}) \cdot |M_i|\right) & \text{si } \varepsilon_i^{\text{eff}} < 0
\end{cases}$$

Con simétricamente `H̃_{i→j}` para el alter.

- `κ` (*kappa*): sesgo de esperanza — amplifica señales positivas cuando el error es positivo.
- `χ` (*chi*): sesgo de amenaza — amplifica señales negativas cuando el error es negativo.
- `|M|`: la historia relacional actúa como **amplificador de sesgo**: a más historia cargada (positiva o negativa), más distorsiona la percepción actual.

> **Justificación:** La percepción social está medida por la historia vincular y el estado interno. Alguien con memoria negativa consolidada (`M << 0`) y sesgo de amenaza alto (`χ > κ`) amplificará cualquier señal ambigua como rechazo, aunque el otro no haya cambiado su conducta. Modela el fenómeno de "negativity bias" y el "confirmation bias" relacional.

---

## 5. Activación Ansiosa Dinámica

La activación ansiosa no es un rasgo fijo, sino que **oscila en respuesta al error**:

$$\tilde{w}_a^{(i)}[t+1] = \tilde{w}_a^{(i)}[t] + \mu_a \cdot \max(0, \varepsilon_i^{\text{eff}}) \cdot |M_i| - \delta_a \cdot (\tilde{w}_a^{(i)} - w_a^{(i)})$$

$$\tilde{w}_a^{(i)} \in [0, 1]$$

- El término `μ_a · max(0, ε_eff) · |M|` escala la ansiedad ante errores positivos acumulados.
- El término `δ_a · (w̃_a - w_a)` actúa como **fuerza restauradora** hacia el rasgo basal `w_a`.

> **Justificación:** La ansiedad de apego no es constante; se activa ante señales de discrepancia con lo esperado, especialmente cuando hay historia relacional significativa. La fuerza restauradora modela la tendencia de los sistemas a regresar a su nivel de rasgo basal (homeostasis del temperamento).

---

## 6. Activación Evitativa Dinámica

La activación evitativa responde a la angustia interna y se inhibe ante señales de seguridad percibidas:

$$\tilde{w}_e^{(i)}[t+1] = \tilde{w}_e^{(i)}[t] + \mu_e \cdot I_i - \delta_e \cdot (\tilde{w}_e^{(i)} - w_e^{(i)}) - \rho_e \cdot \max(0, \hat{H}_{j \to i})$$

$$\tilde{w}_e^{(i)} \in [0, 1]$$

- `μ_e · I`: la angustia acumulada incrementa la tendencia evitativa.
- `ρ_e · max(0, Ĥ)`: las señales prosociales percibidas **reducen** la evitación.

> **Justificación:** La evitación como estrategia regulatoria se activa ante angustia y se desactiva ante seguridad relacional percibida (Mikulincer & Shaver). El término `ρ_e` captura el efecto co-regulatorio: la conducta positiva del otro puede abrir al evitativo, aunque con lentitud.

---

## 7. Emisión Conductual

La conducta observable emerge de la interacción entre recursos prosociales, agotamiento y defensas activas:

$$H_i[t] = \tanh\left( B_i + R_i^{\text{rep}} - \sigma \cdot (\tilde{w}_a^{(i)} + \tilde{w}_e^{(i)}) + \mathcal{N}(0, \sigma_\eta) \right)$$

Donde la **base regulatoria** es:

$$B_i = \underbrace{\lambda_s \cdot w_s^{(i)} \cdot (1 - C_i)}_{\text{núcleo prosocial}} + \underbrace{\left(\lambda_r \cdot R_i^{\text{eff}} + \lambda_g \cdot G_i\right) \cdot (1 - 0.4 \cdot C_i^2)}_{\text{recursos ejecutivos y empatía}}$$

La **capacidad ejecutiva efectiva** decae no linealmente con el burnout:

$$R_i^{\text{eff}} = R_i \cdot (1 - C_i^{q})$$

La **reparación espontánea** ocurre de forma episódica y estocástica:

$$R_i^{\text{rep}} = \begin{cases} r_{\text{strength}} \cdot (1 - 0.35 \cdot C_i) & \text{si } w_e^{(i)} > 0.45 \;\land\; D_j > \theta_r \;\land\; U \sim \text{Bernoulli}(p_r) \\ 0 & \text{en otro caso} \end{cases}$$

donde $D_j = \max(0, -\hat{H}_{j \to i})$ es el **proxy de distrés** inferido conductualmente.

La función `tanh` satura la salida en `[-1, 1]`.

> **Justificación:** La conducta prosocial emerge de recursos limitados y se degrada bajo fatiga. El exponente `q` en el decaimiento de `R_eff` captura el **quiebre prefrontal no lineal**: la capacidad de regulación cae lentamente al inicio y luego colapsa abruptamente (Baumeister, ego depletion; Porges, teoría polivagal). La reparación espontánea es probabilística porque en la realidad los gestos de acercamiento no son deterministas —dependen del umbral de tolerancia, del estado interno y del momento.

---

## 8. Angustia Acumulada

$$I_i[t+1] = \text{clip}\left( I_i[t] + 0.15 \cdot \Delta I_i - \lambda_I \cdot I_i[t],\; 0, 1 \right)$$

Donde el incremento de angustia depende de la señal percibida y la seguridad basal:

$$\Delta I_i = \underbrace{\max(0, -\hat{H}_{j \to i}) \cdot (1 - w_s^{(i)})}_{\text{activación por rechazo percibido}} - \underbrace{\max(0, \hat{H}_{j \to i}) \cdot w_s^{(i)}}_{\text{regulación por señal positiva}}$$

El término `λ_I · I` modela la **disipación espontánea** de angustia en ausencia de estímulos.

> **Justificación:** La angustia se acumula ante señales negativas y se atenúa ante señales de seguridad, con un peso invertamente proporcional a la seguridad basal: un agente con `w_s` alto se regula más fácilmente ante la misma señal positiva. La disipación espontánea refleja la regulación endógena —el sistema nervioso no mantiene activación indefinida sin input.

---

## 9. Burnout Relacional (Carga Alostática)

$$C_i[t+1] = \text{clip}\left( C_i[t] + \Delta C_i,\; 0, 1 \right)$$

$$\Delta C_i = \underbrace{\alpha \cdot I_i}_{\text{costo de angustia}} + \underbrace{\eta_{\text{symp}} \cdot \tilde{w}_a^{(i)} + \eta_{\text{evit}} \cdot \tilde{w}_e^{(i)}}_{\text{costo defensivo}} - \underbrace{\beta \cdot (1 - C_i)^q \cdot w_s^{(i)}}_{\text{clearance alostático}} - \underbrace{\zeta \cdot \max(0, \hat{H}_{j \to i})}_{\text{co-regulación}}$$

- El **costo defensivo** (`η_symp`, `η_evit`) captura el gasto energético de sostener hipervigilancia o evitación activa.
- El **clearance alostático** cae no linealmente: cuando `C` es alto, la recuperación se hace exponencialmente más difícil.
- La **co-regulación** (`ζ`) reduce directamente la carga cuando el otro emite señales positivas.

> **Justificación:** La alostasis (McEwen) describe cómo el organismo mantiene estabilidad pagando un costo energético acumulativo. El burnout relacional modela este proceso: sostener defensas emocionales activas —ansiedad crónica o evitación permanente— tiene un costo metabólico real que se acumula. La co-regulación eficaz (Porges, Feldman) puede reducir esa carga directamente, sin pasar por la angustia. El término no lineal en el clearance captura la histéresis clínica: salir del burnout es más difícil que entrar.

---

## 10. Memoria Relacional

La historia vincular se consolida sobre la **conducta percibida** (no sobre la conducta objetiva):

$$M_i[t+1] = M_i[t] + \gamma^+ \cdot \max(0, \hat{H}_{j \to i}) \cdot (1 - M_i) + \gamma^- \cdot \min(0, \hat{H}_{j \to i}) \cdot (1 + M_i)$$

$$M_i \in [-1, 1]$$

- `γ⁺`: tasa de consolidación de experiencias positivas.
- `γ⁻`: tasa de consolidación de experiencias negativas.
- Los términos `(1 - M)` y `(1 + M)` actúan como **saturación asintótica**: la memoria converge hacia ±1 sin desbordarse.

> **Justificación:** La memoria relacional no es un registro objetivo sino una **reconstrucción subjetiva** influida por el estado interno. Por eso se consolida sobre `Ĥ` (lo percibido) y no sobre `H` (lo emitido). La asimetría entre `γ⁺` y `γ⁻` puede modelar el negativity bias: si `|γ⁻| > γ⁺`, las experiencias negativas se consolidan más rápido, lo que corresponde a la literatura sobre trauma relacional y memoria de trabajo emocional.

---

## 11. Actualización de Expectativas

Las expectativas se actualizan por aprendizaje gradual, modulado por la rigidez:

$$E_i[t+1] = E_i[t] + \nu \cdot (1 - P_i) \cdot \varepsilon_i[t]$$

$$E_i \in [-1, 1]$$

- A mayor `P_i` (rigidez), menor actualización: el agente mantiene sus expectativas a pesar de la evidencia.
- `ν` controla la velocidad general de aprendizaje.

> **Justificación:** Los modelos de trabajo interno (Bowlby) describen cómo las expectativas relacionales se forman en la infancia y son resistentes al cambio. Un agente con `P` alto modela la rigidez de los esquemas de apego consolidados: incluso ante evidencia contraria, el modelo interno se actualiza lentamente. Esto puede generar loops donde el agente "no puede ver" el cambio real del otro porque sus expectativas no se actualizan.

---

## 12. Acoplamiento del Sistema

Las ecuaciones conforman un **sistema dinámico acoplado con retardo** (`τ`). El estado completo del sistema en cada tick es:

$$\mathbf{S}[t] = \left( H_i, H_j, I_i, I_j, C_i, C_j, M_i, M_j, E_i, E_j, \tilde{w}_a^{(i)}, \tilde{w}_a^{(j)}, \tilde{w}_e^{(i)}, \tilde{w}_e^{(j)} \right)$$

El acoplamiento es **bidireccional y asimétrico**: cada agente responde al otro con retardo `τ`, pero sus rasgos, memoria y estado difieren. Esto permite que el sistema converja a distintos **atractores** dependiendo de la configuración inicial y los parámetros.

La perturbación estocástica `N(0, σ_η)` introduce ruido en cada paso, de modo que trayectorias idénticas divergen bajo distintas realizaciones del proceso.

---

## 13. Motor Analítico Post-Simulación

Tras las 500 iteraciones, `analitica.py` computa una **firma fenotípica** sobre las series temporales históricas. Las métricas principales son:

| Métrica | Fórmula / Descripción |
|---------|----------------------|
| **Resonancia retardada** | Correlación de Pearson entre `H_i[t]` y `H_j[t + τ]` |
| **Entropía de fase** | Entropía 2D normalizada del histograma `(H_i, H_j)`: $S = -\sum p_{ij} \log_2 p_{ij} \; / \; \log_2(N^2)$ |
| **Aceleración de angustia** | Velocidad máxima de incremento de `I_i` en ventana deslizante |
| **Eventos de reparación** | Número de spikes positivos en `H_j` con `Δ > r_{\text{strength}}` |
| **Tipo de atractor** | Clasificación por cuadrante de `(mean(H_i), mean(H_j))` |

La **entropía de fase** mide cuán explorado está el espacio de estados relacionales: baja entropía indica un atractor fijo (relación estereotipada); alta entropía indica órbita compleja o caos.

---

## 14. Tabla de Parámetros del Sistema

| Parámetro | Dominio | Rol |
|-----------|---------|-----|
| `λ_s` | `(0, 2)` | Peso del núcleo prosocial en H |
| `λ_r` | `(0, 1)` | Peso de la regulación ejecutiva |
| `λ_g` | `(0, 1)` | Peso de la empatía en H |
| `λ_I` | `(0, 1)` | Tasa de disipación espontánea de I |
| `σ` | `(0, 2)` | Peso del costo defensivo en H |
| `κ` | `(0, 5)` | Sesgo de esperanza en percepción |
| `χ` | `(0, 5)` | Sesgo de amenaza en percepción |
| `α` | `(0, 0.1)` | Tasa de incremento de C por I |
| `β` | `(0, 0.2)` | Tasa de clearance alostático |
| `η_symp` | `(0, 0.02)` | Costo energético de hiperactivación |
| `η_evit` | `(0, 0.02)` | Costo energético de evitación activa |
| `q` | `(1, 5)` | Exponente de quiebre no lineal |
| `γ⁺` | `(0, 0.1)` | Consolidación de memoria positiva |
| `γ⁻` | `(0, 0.1)` | Consolidación de memoria negativa |
| `ν` | `(0, 0.2)` | Velocidad de actualización de E |
| `μ_a` | `(0, 0.5)` | Sensibilidad ansiosa al error |
| `δ_a` | `(0, 0.2)` | Restauración de w̃_a al basal |
| `μ_e` | `(0, 0.5)` | Sensibilidad evitativa a I |
| `δ_e` | `(0, 0.2)` | Restauración de w̃_e al basal |
| `ρ_e` | `(0, 0.2)` | Inhibición evitativa por señal positiva |
| `τ` | `[1, 30]` | Retardo de integración (ticks) |
| `ζ` | `(0, 0.1)` | Efecto co-regulatorio de H̃ positivo |
| `θ_r` | `(0, 1)` | Umbral de distrés para activar reparación |
| `p_r` | `(0, 1)` | Probabilidad de reparación espontánea |
| `r_strength` | `(0, 1)` | Magnitud del boost de reparación |
| `σ_η` | `(0, 0.2)` | Desviación del ruido ambiental |

---

## 15. Propiedades Emergentes

El sistema exhibe las siguientes propiedades que no están codificadas directamente sino que **emergen** de la interacción de las ecuaciones:

**Histéresis alostática.** Salir del burnout es más difícil que entrar, porque el clearance cae no linealmente con `C`. El sistema tiene memoria de sus estados pasados.

**Amplificación sesgada.** El filtro perceptivo con `χ ≠ κ` produce asimetría en la percepción: el mismo comportamiento del otro puede interpretarse como amenaza o como apoyo dependiendo del estado interno del agente. Esto genera bucles de confirmación.

**Desacoplamiento por fatiga.** Cuando `C` sube, la contribución prosocial `λ_s · w_s · (1 - C)` cae linealmente, pero la capacidad ejecutiva `R_eff = R · (1 - C^q)` cae exponencialmente. Esto produce un quiebre asimétrico: el agente puede sostener conducta prosocial por un tiempo incluso bajo burnout alto, pero la capacidad ejecutiva colapsa antes.

**Co-regulación como atenuador sistémico.** El término `ζ` conecta directamente la señal positiva del otro con la reducción de carga alostática, sin pasar por la angustia. Esto produce el fenómeno de "safe haven": la presencia prosocial del otro no solo mejora la conducta sino que reduce el desgaste energético del sistema.

**Reparación como evento de baja probabilidad.** La reparación espontánea es estocástica y condicionada a tres factores simultáneos (`w_e > 0.45`, `D_j > θ_r`, `U < p_r`). Esto reproduce la observación clínica de que la reparación relacional no es automática: requiere disposición, señal clara de distrés y un momento de apertura que no siempre se da.

---

## Referencias conceptuales

- **Teoría del apego:** Bowlby (1969); Ainsworth (1978); Mikulincer & Shaver (2007)
- **Procesamiento predictivo:** Friston (2010); Clark (2016)
- **Alostasis y carga alostática:** McEwen & Stellar (1993); McEwen (1998)
- **Teoría polivagal:** Porges (2011)
- **Regulación emocional diádica:** Feldman (2007); Coan (2008)
- **Negativity bias en memoria:** Baumeister et al. (2001)
- **Sistemas dinámicos en psicología clínica:** Hayes et al. (2007); Vallacher & Nowak (1994)

---

*RA-EEM no constituye herramienta diagnóstica. Su propósito es exploratorio y fenomenológico.*