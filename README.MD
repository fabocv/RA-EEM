# Especificación Arquitectónica: RA-EEM v0.3.3
**Framework de Modelado Dinámico no Lineal para Sistemas Relacionales Complejos**

El modelo **RA-EEM v0.3.3** (Relational Architecture & Emotional Engine Model) formaliza matemáticamente la interacción de dos agentes acoplados mediante flujos asíncronos de información, filtros perceptivos condicionados por la memoria/trauma, y un motor de desgaste energético (*Burnout*) con mecanismos de reparación intermitente y co-regulación cruzada.

---

## 1. Espacio de Estados del Agente

Cada agente representa un sistema dinámico denotado por el subíndice $i$ (siendo $j$ el compañero relacional). Su configuración interna se divide en tres capas según su velocidad operativa.

### A. Rasgos Basales Invariantes (Hardware Psíquico Lento)
* $w_{s,i} \in [0, 1]$: Peso de **Seguridad/Autorregulación** basal.
* $w_{a,i} \in [0, 1]$: Peso de **Reactividad Ansiosa** basal.
* $w_{e,i} \in [0, 1]$: Peso de **Evitación Defensiva** basal.
* $w_{d,i} \in [0, 1]$: Peso de **Desorganización** basal.
* $G_i \in [0, 1]$: Coeficiente de **Heterorregulación/Empatía** identitaria.
* $A_i \in [-1, 1]$: Métrica de **Agencia Estructural**.
* $R_i \in [0, 1]$: Capacidad de **Regulación Consciente / Masking**.

### B. Modos Reactivos Acumuladores (Velocidad Media)
Operan como integradores diferenciales discretos (no sufren sobreescritura inmediata), acumulando inercia frente a shocks y disipando energía hacia sus líneas base estructurales:
* $\tilde{w}_{a,i} \in [0, 1]$: Activación actual del **Modo Ansioso Persecutor**.
* $\tilde{w}_{e,i} \in [0, 1]$: Activación actual del **Modo Evitativo Distanciador**.

### C. Variables de Estado Dinámico (Velocidad Rápida)
* $I_i \in [0, 1]$: **Angustia Latente** (Estado de alarma general del sistema).
* $C_i \in [0, 1]$: **Desgaste Psíquico / Burnout** acumulado.
* $E_i \in [-1, 1]$: **Expectativa Predictiva** sobre la conducta del otro.
* $P_i \in [0, 1]$: **Rigidez Predictiva / Precisión Inferencia** (Resistencia al cambio de $E_i$).
* $M_i \in [-1, 1]$: **Huella de Memoria Relacional** (Clima afectivo histórico acumulado).

---

## 2. Pipeline Operacional por Tick

En cada paso discreto de tiempo $t$, el motor relacional ejecuta secuencialmente las siguientes fases algebraicas:

### Fase 1: Extracción con Delay Coaxial ($\tau$)
El procesamiento cognitivo del agente introduce un desfase temporal. La información conductual del entorno se extrae desde un búfer circular de tamaño $\tau$:
$$H_{j,\text{delayed}} = H_j(t - \tau)$$
$$H_{i,\text{delayed}} = H_i(t - \tau)$$

### Fase 2: Errores Predictivos
El error de predicción bruto $\epsilon_i$ mide la divergencia entre la conducta esperada y la percibida asíncronamente. Se escala por la rigidez de inferencia $P_i$ para obtener el error efectivo $\epsilon_i^{\text{eff}}$:
$$\epsilon_i(t) = H_{j,\text{delayed}} - E_i(t-1)$$
$$\epsilon_i^{\text{eff}}(t) = P_i \cdot \epsilon_i(t)$$

### Fase 3: Modulación del Filtro Perceptivo Saliencial
La conducta retrasada del compañero se distorsiona emocionalmente según el signo del error efectivo y la magnitud de la huella de memoria relacional $M_i$:

$$\hat{H}_{ji} = \begin{cases} 
H_{j,\text{delayed}} \cdot \left(1.0 + \kappa \cdot \max(0.0, \epsilon_i^{\text{eff}}) \cdot |M_i|\right) & \text{si } \epsilon_i^{\text{eff}} \ge 0 \\
H_{j,\text{delayed}} \cdot \left(1.0 + \chi \cdot \max(0.0, -\epsilon_i^{\text{eff}}) \cdot |M_i|\right) & \text{si } \epsilon_i^{\text{eff}} < 0 
\end{cases}$$

> **Nota de asimetría:** Si el error es negativo (amenaza o decepción no anticipada), se aplica el coeficiente de penalización por sesgo defensivo $\chi$, tradicionalmente superior al parámetro de alivio $\kappa$.

### Fase 4: Ecuaciones Diferenciales de Modos Rápidos
Los modos reactivos se modelan como sistemas diferenciales discretos reales con disipación proporcional a la distancia de sus rasgos base ($w_a, w_e$):

* **Modo Ansioso Persecutor ($\tilde{w}_a$):** Se incrementa directamente ante errores predictivos positivos condicionados por el clima histórico.
$$\tilde{w}_{a,i}(t) = \tilde{w}_{a,i}(t-1) + \mu_a \cdot \max(0.0, \epsilon_i^{\text{eff}}) \cdot |M_i| - \delta_a \cdot (\tilde{w}_{a,i}(t-1) - w_{a,i})$$

* **Modo Evitativo Distanciador ($\tilde{w}_e$):** Se incrementa de forma endógena proporcional al nivel de angustia o estrés latente interno $I_i$.
$$\tilde{w}_{e,i}(t) = \tilde{w}_{e,i}(t-1) + \mu_e \cdot I_i(t-1) - \delta_e \cdot (\tilde{w}_{e,i}(t-1) - w_{e,i})$$

### Fase 5: Motor de Emisión Conductual ($H$)
Cada agente proyecta un valor conductual $H \in [-1, 1]$ a través de una función de transferencia no lineal acotada (tangente hiperbólica).

#### Mecanismo de Reparación Intermitente
Si un agente con características evitativas estructurales ($w_{e,i} > 0.45$) detecta que el estrés de su compañero supera el umbral crítico (`repair_threshold`), dispone de una probabilidad estocástica (`repair_probability`) de gatillar un esfuerzo compensatorio de contención relacional:
$$\Omega_{\text{repair}} = \begin{cases} \text{repair\_strength} & \text{si se cumplen las condiciones estocásticas} \\ 0.0 & \text{en cualquier otro caso} \end{cases}$$

#### Ecuación de Emisión Principal
La capacidad pro-social y ejecutiva del agente es comprimida de manera lineal por el nivel de Burnout actual $(1 - C_i)$, mientras que los modos reactivos actúan como fuerzas de sustracción directa. Se inyecta ruido blanco gaussiano para simular perturbaciones ambientales:
$$\text{raw}_i = \left(\lambda_s w_{s,i} + \lambda_r R_i + \lambda_g G_i + \Omega_{\text{repair}}\right) \cdot (1.0 - C_i) - \sigma \cdot (\tilde{w}_{a,i} + \tilde{w}_{e,i})$$
$$H_i(t) = \tanh\left(	ext{raw}_i + \mathcal{N}(0, \sigma_{\text{noise}}^2)\right)$$

### Fase 6: Homeostasis Afectiva (Angustia y Carga Alostática)
* **Dinámica de Angustia Latente ($I$):** Alterada por el signo de la conducta filtrada del compañero. Emisiones percibidas como hostiles ($\hat{H} < 0$) elevan la angustia en proporción a la vulnerabilidad del sujeto $(1 - w_s)$. Conductas prosociales la mitigan utilizando la base de seguridad $w_s$.
$$\Delta I_i = \max(0.0, -\hat{H}_{ji}) \cdot (1.0 - w_{s,i}) - \max(0.0, \hat{H}_{ji}) \cdot w_{s,i}$$
$$I_i(t) = \text{clip}(I_i(t-1) + \Delta I_i, 0.0, 1.0)$$

* **Dinámica de Burnout / Desgaste Energético ($C$):** La angustia sostenida inyecta fatiga a una tasa $\alpha$. La recuperación metabólica autónoma $\beta$ está penalizada por el exponente de histéresis crónico $p_{\text{burnout}}$ y protegida por la seguridad $w_s$. Adicionalmente, se introduce el amortiguador de **co-regulación cruzada** $\zeta$, donde las conductas prosociales efectivas del compañero alivian directamente el desgaste energético:
$$\Delta C_i = \alpha \cdot I_i - \beta \cdot (1.0 - C_i)^{p_{\text{burnout}}} \cdot w_{s,i} - \zeta \cdot \max(0.0, H_j)$$
$$C_i(t) = \text{clip}(C_i(t-1) + \Delta C_i, 0.0, 1.0)$$

### Fase 7: Plasticidad de Memoria Relacional y Deriva de Expectativas
* **Memoria Histórica Relacional ($M$):** Almacena el clima vincular promedio mediante tasas asimétricas de consolidación para experiencias positivas ($\gamma_+$) y traumáticas o negativas ($\gamma_-$).
$$\Delta M_i = \gamma_+ \cdot \max(0.0, H_j) \cdot (1.0 - M_i) + \gamma_- \cdot \min(0.0, H_j) \cdot (1.0 + M_i)$$
$$M_i(t) = \text{clip}(M_i(t-1) + \Delta M_i, -1.0, 1.0)$$

* **Deriva del Modelo de Expectativas ($E$):** Las expectativas internas se desplazan de manera adaptativa hacia el comportamiento observado a una tasa de aprendizaje $\nu$, obstaculizada si la rigidez predictiva $P_i$ es elevada.
$$E_i(t) = E_i(t-1) + \nu \cdot (1.0 - P_i) \cdot \epsilon_i(t)$$

---

## 3. Matriz de Hiperparámetros Calibrados (Configuración v0.3.3)

| Parámetro | Valor Numérico | Dominio Funcional y Conceptual |
| :--- | :--- | :--- |
| `lambda_s` | 1.2 | Peso del apego seguro autónomo en la emisión conductual. |
| `lambda_r` | 0.5 | Capacidad de control ejecutivo consciente / Regulación activa. |
| `lambda_g` | 0.3 | Ponderación del acoplamiento empático heterorregulatorio. |
| `sigma` | 1.0 | Multiplicador de impacto de las activaciones defensivas rápidas. |
| `kappa` | 1.6 | Ganancia perceptiva frente a errores de predicción positivos. |
| `chi` | 2.2 | Sesgo de negatividad amplificado ante errores negativos (Amenazas). |
| `alpha` | 0.04 | Tasa de inyección de angustia activa en desgaste psicofísico crónico. |
| `beta` | 0.12 | Capacidad basal de metabolismo y disipación de la fatiga. |
| `p_burnout` | 1.5 | Exponente de histéresis no lineal para simular el anclaje del agotamiento. |
| `gamma_plus`| 0.015 | Velocidad de consolidación de confianza histórica en la memoria. |
| `gamma_minus`| 0.04 | Velocidad de erosión y fijación de traumas en la memoria vincular. |
| `nu` | 0.08 | Tasa base de actualización adaptativa del modelo interno (Inferencia). |
| `mu_a` | 0.2 | Tasa de inyección del error en el acumulador del modo ansioso. |
| `delta_a` | 0.08 | Coeficiente de disipación y relajación del modo ansioso. |
| `mu_e` | 0.1 | Tasa de conversión de angustia interna en repliegue evitativo. |
| `delta_e` | 0.05 | Coeficiente de disipación y relajación del modo evitativo. |
| `tau` | 10 | Retraso temporal (ticks) del buffer de transporte de información. |
| `repair_threshold` | 0.6 | Nivel de estrés del compañero requerido para gatillar reparación. |
| `repair_probability`| 0.12 | Probabilidad por tick de que un evitativo rompa su defensa para asistir. |
| `repair_strength` | 0.8 | Magnitud del impulso prosocial artificial inyectado en la reparación. |
| `zeta` | 0.03 | Co-regulación cruzada: alivio alostático inducido por la bondad del otro. |
| `noise_sigma` | 0.015 | Desviación estándar del ruido estocástico e indeterminado del entorno. |
