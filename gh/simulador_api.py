# ============================================================
# RA-EEM v0.3.5 — API VERSION
# Modificado para retornar imagen base64 + JSON en vez de plt.show()
#
# CAMBIOS v0.3.5 vs v0.3.4:
#   FIX-1 [CRÍTICO]  emit_behavior() ahora se llama en step()
#   FIX-2 [CRÍTICO]  Asimetría temporal en inhibición cruzada corregida
#                    (snapshots wa/we_t antes de cualquier actualización)
#   FIX-3 [MEDIO]    E se actualiza con aprendizaje lento ν·(1−P)·eps
#   FIX-4 [MEDIO]    M clipeado a [−1, 1] después de fragmentación
#   FIX-5 [BAJO]     history extendido: M, wa, we registrados
#   FIX-6 [INFO]     wd_cross_inhibit usado en wd_modulated_restore()
# ============================================================

import io
import base64
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')  # CRÍTICO: backend sin GUI para servidor
import matplotlib.pyplot as plt

from dataclasses import dataclass, field
from collections import deque


# ============================================================
# AGENTE
# ============================================================

@dataclass
class Agent:

    w_s: float
    w_a: float
    w_e: float
    w_d: float

    G: float
    A: float

    I: float = 0.0
    C: float = 0.0

    E: float = 0.0
    P: float = 0.8

    M: float = 0.0

    R: float = 0.5

    w_tilde_a: float = field(init=False)
    w_tilde_e: float = field(init=False)

    def __post_init__(self):
        self.w_tilde_a = self.w_a
        self.w_tilde_e = self.w_e


# ============================================================
# SIMULADOR
# ============================================================

class RAEEMSimulation:

    def __init__(self, agent_i, agent_j, params):
        self.i = agent_i
        self.j = agent_j
        self.p = params

        self.H_i = 0.0
        self.H_j = 0.0

        self.H_i_history = deque([0.0] * self.p["tau"], maxlen=self.p["tau"])
        self.H_j_history = deque([0.0] * self.p["tau"], maxlen=self.p["tau"])
        self.graph_metrics = {
            "restore_a_i": [],
            "restore_e_i": [],
            "restore_a_j": [],
            "restore_e_j": [],
            "phi_d_i": [],
            "phi_d_j": [],
        }

    def perceptual_filter(self, H, eps_eff, M):
        if eps_eff >= 0:
            return H * (1.0 + self.p["kappa"] * max(0.0, eps_eff) * abs(M))
        else:
            return H * (1.0 + self.p["chi"] * max(0.0, -eps_eff) * abs(M))

    def emit_behavior(self, ag, perceived_H_hat_partner):
        p = self.p
        perceived_partner_distress = max(0.0, -perceived_H_hat_partner)
        repair_boost = 0.0

        if (
            ag.w_e > 0.45
            and perceived_partner_distress > p["repair_threshold"]
            and np.random.rand() < p["repair_probability"]
        ):
            repair_boost = p["repair_strength"]

        R_eff = ag.R * (1.0 - ag.C ** p["q_fatigue"])
        prosocial_core = p["lambda_s"] * ag.w_s * (1.0 - ag.C)
        willpower_core = (p["lambda_r"] * R_eff + p["lambda_g"] * ag.G) * (1.0 - 0.4 * ag.C**2)
        baseline_regulation = prosocial_core + willpower_core
        repair_component = repair_boost * (1.0 - 0.35 * ag.C)

        raw = (
            baseline_regulation
            + repair_component
            - p["sigma"] * (ag.w_tilde_a + ag.w_tilde_e)
        )

        # ============================================================
        # VOLATILIDAD DESORGANIZADA (Componente 2 — Φ_d)
        # ============================================================
        phi_d = (
            1.0
            + ag.w_d
            * ((ag.w_tilde_a + ag.w_tilde_e) / 2.0)
            * p["wd_noise_gain"]
        )

        noise = np.random.normal(0, p["noise_sigma"] * phi_d)
        raw += noise

        return np.tanh(raw)

    def wd_modulated_restore(self, delta, w_d, opposite_activation):
        """
        Restauración degradada por desorganización.
        FIX-6: usa wd_cross_inhibit como parámetro controlable.
        Con wd_cross_inhibit=0 se desactiva la inhibición cruzada
        para experimentos de aislamiento de componentes.
        """
        cross = self.p.get("wd_cross_inhibit", 1.0)
        return delta * (1.0 - w_d * opposite_activation * cross)

    def step(self):
        p = self.p

        # ── Señales retrasadas ───────────────────────────────────
        delayed_H_i = self.H_i_history[0]
        delayed_H_j = self.H_j_history[0]

        # ── Error predictivo ────────────────────────────────────
        eps_i = delayed_H_j - self.i.E
        eps_j = delayed_H_i - self.j.E

        eps_eff_i = self.i.P * eps_i
        eps_eff_j = self.j.P * eps_j

        # ── FIX-3: Actualización de expectativas E ───────────────
        # E se actualiza lentamente con tasa ν·(1−P).
        # Agente rígido (P→1): E casi no cambia.
        # Agente plástico (P→0): E sigue la señal más de cerca.
        # Activa el loop L4 (expectativa-rigidez) correctamente.
        nu = p.get("nu", 0.02)
        self.i.E += nu * (1.0 - self.i.P) * eps_i
        self.j.E += nu * (1.0 - self.j.P) * eps_j

        # ── Filtro perceptivo ────────────────────────────────────
        H_hat_ji = self.perceptual_filter(delayed_H_j, eps_eff_i, self.i.M)
        H_hat_ij = self.perceptual_filter(delayed_H_i, eps_eff_j, self.j.M)

        # ── FIX-1: Emisión conductual ────────────────────────────
        # emit_behavior() se llama aquí, después de calcular H_hat
        # (que depende de señales retrasadas) y antes de actualizar
        # el historial. Resuelve el bug donde H_i/H_j eran 0 siempre.
        self.H_i = self.emit_behavior(self.i, H_hat_ji)
        self.H_j = self.emit_behavior(self.j, H_hat_ij)

        # ── FIX-2: Snapshots para inhibición cruzada simétrica ───
        # Guardamos w̃ₐ y w̃ₑ del tick t ANTES de cualquier
        # actualización. Así restore_a y restore_e ven los mismos
        # valores del tick t, eliminando la asimetría temporal.
        wa_i_t = self.i.w_tilde_a
        we_i_t = self.i.w_tilde_e
        wa_j_t = self.j.w_tilde_a
        we_j_t = self.j.w_tilde_e

        # ── Activación ansiosa (inhibición cruzada simétrica) ────
        restore_i_a = self.wd_modulated_restore(p["delta_a"], self.i.w_d, we_i_t)
        restore_j_a = self.wd_modulated_restore(p["delta_a"], self.j.w_d, we_j_t)

        self.i.w_tilde_a += (
            p["mu_a"] * max(0.0, eps_eff_i) * abs(self.i.M)
            - restore_i_a * (self.i.w_tilde_a - self.i.w_a)
        )
        self.j.w_tilde_a += (
            p["mu_a"] * max(0.0, eps_eff_j) * abs(self.j.M)
            - restore_j_a * (self.j.w_tilde_a - self.j.w_a)
        )

        self.i.w_tilde_a = np.clip(self.i.w_tilde_a, 0.0, 1.0)
        self.j.w_tilde_a = np.clip(self.j.w_tilde_a, 0.0, 1.0)

        # ── Activación evitativa (inhibición cruzada simétrica) ──
        # FIX-2: restore_e usa wa_i_t (snapshot t), no w_tilde_a
        # que ya fue actualizado arriba.
        restore_i_e = self.wd_modulated_restore(p["delta_e"], self.i.w_d, wa_i_t)
        restore_j_e = self.wd_modulated_restore(p["delta_e"], self.j.w_d, wa_j_t)

        rho_i_eff = p["rho_e"] * (1.0 - self.i.w_d * p["wd_coreg_loss"])
        rho_j_eff = p["rho_e"] * (1.0 - self.j.w_d * p["wd_coreg_loss"])

        self.i.w_tilde_e += (
            p["mu_e"] * self.i.I
            - restore_i_e * (self.i.w_tilde_e - self.i.w_e)
            - rho_i_eff * max(0.0, H_hat_ji)
        )
        self.j.w_tilde_e += (
            p["mu_e"] * self.j.I
            - restore_j_e * (self.j.w_tilde_e - self.j.w_e)
            - rho_j_eff * max(0.0, H_hat_ij)
        )

        self.i.w_tilde_e = np.clip(self.i.w_tilde_e, 0.0, 1.0)
        self.j.w_tilde_e = np.clip(self.j.w_tilde_e, 0.0, 1.0)

        # ── Registro de métricas de grafo ────────────────────────
        self.graph_metrics["restore_a_i"].append(restore_i_a)
        self.graph_metrics["restore_e_i"].append(restore_i_e)
        self.graph_metrics["restore_a_j"].append(restore_j_a)
        self.graph_metrics["restore_e_j"].append(restore_j_e)
        self.graph_metrics["phi_d_i"].append(
            1.0 + self.i.w_d * ((self.i.w_tilde_a + self.i.w_tilde_e) / 2.0)
        )
        self.graph_metrics["phi_d_j"].append(
            1.0 + self.j.w_d * ((self.j.w_tilde_a + self.j.w_tilde_e) / 2.0)
        )

        # ── Angustia ─────────────────────────────────────────────
        delta_I_i = max(0.0, -H_hat_ji) * (1.0 - self.i.w_s) - max(0.0, H_hat_ji) * self.i.w_s
        delta_I_j = max(0.0, -H_hat_ij) * (1.0 - self.j.w_s) - max(0.0, H_hat_ij) * self.j.w_s

        self.i.I = np.clip(self.i.I + 0.15 * delta_I_i - p["lambda_I"] * self.i.I, 0.0, 1.0)
        self.j.I = np.clip(self.j.I + 0.15 * delta_I_j - p["lambda_I"] * self.j.I, 0.0, 1.0)

        # ── Burnout ──────────────────────────────────────────────
        costo_defensivo_i = p["eta_symp"] * self.i.w_tilde_a + p["eta_evit"] * self.i.w_tilde_e
        clearance_i = p["beta"] * ((1.0 - self.i.C) ** p["q_fatigue"]) * self.i.w_s
        delta_C_i = p["alpha"] * self.i.I + costo_defensivo_i - clearance_i - p["zeta"] * max(0.0, H_hat_ji)

        costo_defensivo_j = p["eta_symp"] * self.j.w_tilde_a + p["eta_evit"] * self.j.w_tilde_e
        clearance_j = p["beta"] * ((1.0 - self.j.C) ** p["q_fatigue"]) * self.j.w_s
        delta_C_j = p["alpha"] * self.j.I + costo_defensivo_j - clearance_j - p["zeta"] * max(0.0, H_hat_ij)

        self.i.C = np.clip(self.i.C + delta_C_i, 0.0, 1.0)
        self.j.C = np.clip(self.j.C + delta_C_j, 0.0, 1.0)

        # ── Memoria relacional ───────────────────────────────────
        self.i.M += (
            p["gamma_plus"] * max(0.0, H_hat_ji) * (1.0 - self.i.M)
            + p["gamma_minus"] * min(0.0, H_hat_ji) * (1.0 + self.i.M)
        )
        self.j.M += (
            p["gamma_plus"] * max(0.0, H_hat_ij) * (1.0 - self.j.M)
            + p["gamma_minus"] * min(0.0, H_hat_ij) * (1.0 + self.j.M)
        )

        # ── Fragmentación desorganizada (Componente 3 — ξ_d) ────
        p_d_i = p["p_d_base"] * self.i.w_d
        p_d_j = p["p_d_base"] * self.j.w_d

        if np.random.rand() < p_d_i:
            self.i.M *= (1.0 - p["memory_erosion"] * self.i.w_d)

        if np.random.rand() < p_d_j:
            self.j.M *= (1.0 - p["memory_erosion"] * self.j.w_d)

        # ── FIX-4: Clip de M a [−1, 1] ──────────────────────────
        # La formalización del loop L2 establece que el dominio de
        # M es estrictamente [−1, 1]. El clip previene deriva numérica
        # por amplificación del filtro perceptivo o acumulación en
        # la fragmentación estocástica.
        self.i.M = np.clip(self.i.M, -1.0, 1.0)
        self.j.M = np.clip(self.j.M, -1.0, 1.0)

        # ── Métrica de fragilidad dinámica ───────────────────────
        fragility_i = self.i.w_tilde_a * self.i.w_tilde_e * self.i.w_d
        fragility_j = self.j.w_tilde_a * self.j.w_tilde_e * self.j.w_d

        # ── Avanzar historial ────────────────────────────────────
        self.H_i_history.append(self.H_i)
        self.H_j_history.append(self.H_j)

        return {

            # ========================================================
            # COMPORTAMIENTO
            # ========================================================

            "H_i": self.H_i,
            "H_j": self.H_j,

            # ========================================================
            # ANGUSTIA
            # ========================================================

            "I_i": self.i.I,
            "I_j": self.j.I,

            # ========================================================
            # BURNOUT
            # ========================================================

            "C_i": self.i.C,
            "C_j": self.j.C,

            # ========================================================
            # MEMORIA RELACIONAL
            # ========================================================

            "M_i": self.i.M,
            "M_j": self.j.M,

            # ========================================================
            # EXPECTATIVAS
            # ========================================================

            "E_i": self.i.E,
            "E_j": self.j.E,

            # ========================================================
            # ACTIVACIONES DEFENSIVAS
            # ========================================================

            "wa_i": self.i.w_tilde_a,
            "wa_j": self.j.w_tilde_a,

            "we_i": self.i.w_tilde_e,
            "we_j": self.j.w_tilde_e,

            # ========================================================
            # ERRORES PREDICTIVOS
            # ========================================================

            "eps_i": eps_i,
            "eps_j": eps_j,

            # ========================================================
            # PERCEPCIONES FILTRADAS
            # ========================================================

            "H_hat_ij": H_hat_ij,
        }


def generate_agents_from_system_params(params):

    params.update({
        # --- desorganización ---
        "p_d_base":        0.08,   # probabilidad base fragmentación memoria
        "memory_erosion":  0.35,   # fuerza erosiva
        "wd_cross_inhibit": 1.0,   # FIX-6: fuerza inhibición cruzada (0=desactivada)
        "wd_noise_gain":   1.0,    # amplificación volatilidad
        "wd_coreg_loss":   1.0,    # degradación coregulación
    })

    prof_i = params["_derived_agent_profile"]
    agent_i = Agent(
        w_s=prof_i["w_s"], w_a=prof_i["w_a"], w_e=prof_i["w_e"], w_d=prof_i["w_d"],
        G=prof_i.get("G", 0.5), A=prof_i["A"], P=prof_i["P_default"]
    )

    alter_cfg = params["_alter_settings"]
    prof_j = alter_cfg.get("custom_profile") or {
        "w_s": 0.40, "w_a": 0.20, "w_e": 0.20, "w_d": 0.20,
        "G": 0.4, "A": 0.0, "P_default": 0.70
    }
    agent_j = Agent(
        w_s=prof_j["w_s"], w_a=prof_j["w_a"], w_e=prof_j["w_e"], w_d=prof_j["w_d"],
        G=prof_j.get("G", 0.5), A=prof_j["A"], P=prof_j["P_default"]
    )
    return agent_i, agent_j


def simular_api(params: dict) -> dict:
    """
    Versión API del simulador.
    Retorna: { "phenotype": {...}, "image_base64": "data:image/png;base64,..." }
    """
    from analitica import compute_phenotype_signature

    params = dict(params)
    params['noise_sigma'] = params.get('noise_sigma', 0.05)

    sujeto_i, companero_j = generate_agents_from_system_params(params)

    sim = RAEEMSimulation(sujeto_i, companero_j, params)
    ticks = 500

    # ── FIX-5: History extendido ──────────────────────────────────
    # Se agregan M, wa, we para habilitar:
    #   - análisis de distribución de atractores (loop L2)
    #   - verificación post-hoc de condición de estabilidad L1
    #   - análisis de cuencas de atracción en Nivel 2
    
    history = {

        # ========================================================
        # COMPORTAMIENTO
        # ========================================================

        "H_i": [],
        "H_j": [],

        # ========================================================
        # ANGUSTIA
        # ========================================================

        "I_i": [],
        "I_j": [],

        # ========================================================
        # BURNOUT
        # ========================================================

        "C_i": [],
        "C_j": [],

        # ========================================================
        # MEMORIA
        # ========================================================

        "M_i": [],
        "M_j": [],

        # ========================================================
        # EXPECTATIVAS
        # ========================================================

        "E_i": [],
        "E_j": [],

        # ========================================================
        # ACTIVACIONES DEFENSIVAS
        # ========================================================

        "wa_i": [],
        "wa_j": [],

        "we_i": [],
        "we_j": [],

        # ========================================================
        # OPCIONALES
        # ========================================================

        "eps_i": [],
        "eps_j": [],

        "H_hat_ij": [],
        "H_hat_ji": [],
    }

    for _ in range(ticks):
        state = sim.step()
        for k in history:
            history[k].append(state[k])

    # Firma fenotípica
    phenotype = compute_phenotype_signature(history, params)

    from topology import analyze_dyadic_coupling

    level2 = analyze_dyadic_coupling(
        history,
        theta=params.get("graph_theta", 0.3)
    )


    # ── Gráfica ───────────────────────────────────────────────────
    fig = plt.figure(figsize=(14, 10), facecolor='#0d1117')

    ax1 = plt.subplot(2, 2, 1)
    ax1.set_facecolor('#0d1117')
    ax1.plot(history["H_i"], label="Sujeto (i)", color='#58a6ff', linewidth=1.2)
    ax1.plot(history["H_j"], label="Alter (j)", color='#f97316', linewidth=1.2)
    ax1.axhline(0, linestyle="--", alpha=0.3, color='white')
    ax1.set_title("Emisión Conductual", color='white', fontsize=11)
    ax1.set_xlabel("Ticks", color='#8b949e')
    ax1.set_ylabel("H", color='#8b949e')
    ax1.tick_params(colors='#8b949e')
    ax1.legend(facecolor='#161b22', labelcolor='white', edgecolor='#30363d')
    for spine in ax1.spines.values():
        spine.set_edgecolor('#30363d')

    ax2 = plt.subplot(2, 2, 2)
    ax2.set_facecolor('#0d1117')
    ax2.plot(history["C_i"], label="Burnout Sujeto", color='#58a6ff', linewidth=1.2)
    ax2.plot(history["C_j"], label="Burnout Alter", color='#f97316', linewidth=1.2)
    ax2.plot(history["I_i"], alpha=0.6, label="Angustia Sujeto", color='#3fb950', linewidth=1.0)
    ax2.plot(history["I_j"], alpha=0.6, label="Angustia Alter", color='#ff7b72', linewidth=1.0)
    ax2.set_title("Carga Energética", color='white', fontsize=11)
    ax2.set_xlabel("Ticks", color='#8b949e')
    ax2.set_ylabel("[0,1]", color='#8b949e')
    ax2.tick_params(colors='#8b949e')
    ax2.legend(facecolor='#161b22', labelcolor='white', edgecolor='#30363d')
    for spine in ax2.spines.values():
        spine.set_edgecolor('#30363d')

    ax3 = plt.subplot(2, 1, 2)
    ax3.set_facecolor('#0d1117')
    colors_t = np.arange(ticks)
    sc = ax3.scatter(history["H_i"], history["H_j"], c=colors_t, cmap="plasma", s=20, alpha=0.8)
    ax3.plot(history["H_i"], history["H_j"], alpha=0.2, color='white', linewidth=0.5)
    ax3.scatter(history["H_i"][0], history["H_j"][0], s=120, color="#3fb950", label="Inicio", zorder=5)
    ax3.scatter(history["H_i"][-1], history["H_j"][-1], s=120, color="#ff7b72", label="Fin", zorder=5)
    ax3.axhline(0, linestyle="--", alpha=0.2, color='white')
    ax3.axvline(0, linestyle="--", alpha=0.2, color='white')
    ax3.set_xlabel("H Sujeto (i)", color='#8b949e')
    ax3.set_ylabel("H Alter (j)", color='#8b949e')
    ax3.set_title("Retrato de Fase Relacional", color='white', fontsize=11)
    ax3.tick_params(colors='#8b949e')
    ax3.legend(facecolor='#161b22', labelcolor='white', edgecolor='#30363d')
    for spine in ax3.spines.values():
        spine.set_edgecolor('#30363d')
    cbar = plt.colorbar(sc, ax=ax3, label="Tiempo")
    cbar.ax.yaxis.label.set_color('white')
    cbar.ax.tick_params(colors='#8b949e')

    plt.tight_layout(pad=2.0)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120, bbox_inches='tight', facecolor='#0d1117')
    plt.close(fig)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')

    return {
        "model": {
            "name": "RA-EEM",
            "version": "0.3.5",
            "schema_version": "topology-level2",
            "build": "2026-05-27"
        },

        "phenotype": phenotype,

        "topology": topology,

        "history": history,
        
        "image_base64": f"data:image/png;base64,{img_b64}"
    }