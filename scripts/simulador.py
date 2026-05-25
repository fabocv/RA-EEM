# ============================================================
# RA-EEM v0.3.4
# Simulación Completa + Gráficas
# Correcciones aplicadas:
#   1. Clip de w_tilde_a y w_tilde_e a [0,1]
#   2. Co-regulación (zeta) sobre H_hat percibido, no H crudo
#   3. Memoria relacional consolidada sobre H_hat percibido
#   4. Proxy de distrés inferido conductualmente (no acceso a I interno)
#   5. Clip de expectativas E a [-1,1]
# ============================================================

import numpy as np
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

        self.H_i_history = deque(
            [0.0] * self.p["tau"],
            maxlen=self.p["tau"]
        )

        self.H_j_history = deque(
            [0.0] * self.p["tau"],
            maxlen=self.p["tau"]
        )

    # ========================================================

    def perceptual_filter(self, H, eps_eff, M):

        if eps_eff >= 0:

            return H * (
                1.0
                + self.p["kappa"]
                * max(0.0, eps_eff)
                * abs(M)
            )

        else:

            return H * (
                1.0
                + self.p["chi"]
                * max(0.0, -eps_eff)
                * abs(M)
            )

    # ========================================================

    def emit_behavior(self, ag, perceived_H_hat_partner):
        """
        perceived_H_hat_partner: conducta percibida (filtrada) del compañero.
        El proxy de distrés se infiere conductualmente desde señales
        negativas observadas — el agente no tiene acceso al estado
        interno real del otro.
        """

        p = self.p

        # Proxy de distrés: señales hostiles/negativas percibidas
        perceived_partner_distress = max(0.0, -perceived_H_hat_partner)

        repair_boost = 0.0

        # Reparación intermitente
        if (
            ag.w_e > 0.45
            and perceived_partner_distress > p["repair_threshold"]
            and np.random.rand() < p["repair_probability"]
        ):

            repair_boost = p["repair_strength"]

        # Fatiga ejecutiva no lineal: el Masking resiste hasta el quiebre abrupto
        R_eff = ag.R * (1.0 - ag.C ** p["q_fatigue"])

        prosocial_core = p["lambda_s"] * ag.w_s * (1.0 - ag.C)
        willpower_core = (p["lambda_r"] * R_eff + p["lambda_g"] * ag.G) * (1.0 - 0.4 * ag.C**2)

        baseline_regulation = prosocial_core + willpower_core

        # La reparación episódica bypasséa parcialmente el burnout
        repair_component = (
            repair_boost
            * (1.0 - 0.35 * ag.C)
        )

        raw = (
            baseline_regulation
            + repair_component
            - p["sigma"]
            * (
                ag.w_tilde_a
                + ag.w_tilde_e
            )
        )

        raw += np.random.normal(
            0,
            p["noise_sigma"]
        )

        return np.tanh(raw)

    # ========================================================

    def step(self):

        p = self.p

        delayed_H_i = self.H_i_history[0]
        delayed_H_j = self.H_j_history[0]

        # ----------------------------------------------------
        # Error predictivo
        # ----------------------------------------------------

        eps_i = delayed_H_j - self.i.E
        eps_j = delayed_H_i - self.j.E

        eps_eff_i = self.i.P * eps_i
        eps_eff_j = self.j.P * eps_j

        # ----------------------------------------------------
        # Percepción
        # ----------------------------------------------------

        H_hat_ji = self.perceptual_filter(
            delayed_H_j,
            eps_eff_i,
            self.i.M
        )

        H_hat_ij = self.perceptual_filter(
            delayed_H_i,
            eps_eff_j,
            self.j.M
        )

        # ----------------------------------------------------
        # Activación ansiosa
        # ----------------------------------------------------

        self.i.w_tilde_a += (
            p["mu_a"]
            * max(0.0, eps_eff_i)
            * abs(self.i.M)
            -
            p["delta_a"]
            * (
                self.i.w_tilde_a
                - self.i.w_a
            )
        )

        self.j.w_tilde_a += (
            p["mu_a"]
            * max(0.0, eps_eff_j)
            * abs(self.j.M)
            -
            p["delta_a"]
            * (
                self.j.w_tilde_a
                - self.j.w_a
            )
        )

        # Clip: w_tilde debe permanecer en [0, 1] — sin esto puede
        # desbordarse con errores grandes en los primeros ticks
        self.i.w_tilde_a = np.clip(self.i.w_tilde_a, 0.0, 1.0)
        self.j.w_tilde_a = np.clip(self.j.w_tilde_a, 0.0, 1.0)

        # ----------------------------------------------------
        # Activación evitativa
        # ----------------------------------------------------

        self.i.w_tilde_e += (
            p["mu_e"] * self.i.I
            -
            p["delta_e"] * (
                self.i.w_tilde_e - self.i.w_e
            )
            -
            p["rho_e"] * max(0.0, H_hat_ji)
        )

        self.j.w_tilde_e += (
            p["mu_e"] * self.j.I
            -
            p["delta_e"] * (
                self.j.w_tilde_e - self.j.w_e
            )
            -
            p["rho_e"] * max(0.0, H_hat_ij)
        )

        # Clip: ídem para modo evitativo
        self.i.w_tilde_e = np.clip(self.i.w_tilde_e, 0.0, 1.0)
        self.j.w_tilde_e = np.clip(self.j.w_tilde_e, 0.0, 1.0)

        # ----------------------------------------------------
        # Emisión conductual
        # ----------------------------------------------------

        # Se pasa H_hat del compañero (percibido, filtrado) como señal
        # de distrés observable — no el estado interno I directamente.
        self.H_i = self.emit_behavior(
            self.i,
            H_hat_ij   # i percibe a j a través de H_hat_ji; j percibe a i a través de H_hat_ij
        )

        self.H_j = self.emit_behavior(
            self.j,
            H_hat_ji
        )

        # ----------------------------------------------------
        # Angustia
        # ----------------------------------------------------

        delta_I_i = (
            max(0.0, -H_hat_ji)
            * (1.0 - self.i.w_s)
            -
            max(0.0, H_hat_ji)
            * self.i.w_s
        )

        delta_I_j = (
            max(0.0, -H_hat_ij)
            * (1.0 - self.j.w_s)
            -
            max(0.0, H_hat_ij)
            * self.j.w_s
        )

        self.i.I = np.clip(
            self.i.I
            + 0.15 * delta_I_i
            - p["lambda_I"] * self.i.I,
            0.0,
            1.0
        )

        self.j.I = np.clip(
            self.j.I
            + 0.15 * delta_I_j
            - p["lambda_I"] * self.j.I,
            0.0,
            1.0
        )

        # ----------------------------------------------------
        # Burnout
        # ----------------------------------------------------

        # Agent I (Ansioso)
        costo_defensivo_i = (
            p["eta_symp"] * self.i.w_tilde_a 
            + p["eta_evit"] * self.i.w_tilde_e
        )
        # Quiebre prefrontal: a mayor burnout, la recuperación (beta) cae de forma no lineal
        clearance_i = p["beta"] * ((1.0 - self.i.C) ** p["q_fatigue"]) * self.i.w_s

        delta_C_i = (
            p["alpha"] * self.i.I
            + costo_defensivo_i
            - clearance_i
            - p["zeta"] * max(0.0, H_hat_ji)
        )

        # Agent J (Evitativo)
        costo_defensivo_j = (
            p["eta_symp"] * self.j.w_tilde_a 
            + p["eta_evit"] * self.j.w_tilde_e
        )
        clearance_j = p["beta"] * ((1.0 - self.j.C) ** p["q_fatigue"]) * self.j.w_s

        delta_C_j = (
            p["alpha"] * self.j.I
            + costo_defensivo_j
            - clearance_j
            - p["zeta"] * max(0.0, H_hat_ij)
        )

        self.i.C = np.clip(self.i.C + delta_C_i, 0.0, 1.0)
        self.j.C = np.clip(self.j.C + delta_C_j, 0.0, 1.0)

        # ----------------------------------------------------
        # Memoria relacional
        # ----------------------------------------------------

        # Memoria consolidada sobre la conducta PERCIBIDA (H_hat):
        # la historia relacional se construye desde la experiencia
        # subjetiva del agente, no desde la emisión objetiva del otro.
        self.i.M += (
            p["gamma_plus"]
            * max(0.0, H_hat_ji)
            * (1.0 - self.i.M)
            +
            p["gamma_minus"]
            * min(0.0, H_hat_ji)
            * (1.0 + self.i.M)
        )

        self.j.M += (
            p["gamma_plus"]
            * max(0.0, H_hat_ij)
            * (1.0 - self.j.M)
            +
            p["gamma_minus"]
            * min(0.0, H_hat_ij)
            * (1.0 + self.j.M)
        )

        self.i.M = np.clip(self.i.M, -1.0, 1.0)
        self.j.M = np.clip(self.j.M, -1.0, 1.0)

        # ----------------------------------------------------
        # Expectativas
        # ----------------------------------------------------

        self.i.E += (
            p["nu"]
            * (1.0 - self.i.P)
            * eps_i
        )

        self.j.E += (
            p["nu"]
            * (1.0 - self.j.P)
            * eps_j
        )

        # Clip de expectativas: E debe mantenerse en el mismo rango que H
        # para evitar que los errores predictivos diverjan ilimitadamente
        self.i.E = np.clip(self.i.E, -1.0, 1.0)
        self.j.E = np.clip(self.j.E, -1.0, 1.0)

        # ----------------------------------------------------
        # Delay update
        # ----------------------------------------------------

        self.H_i_history.append(self.H_i)
        self.H_j_history.append(self.H_j)

        return {
            "H_i": self.H_i,
            "H_j": self.H_j,
            "I_i": self.i.I,
            "I_j": self.j.I,
            "C_i": self.i.C,
            "C_j": self.j.C,
        }

def generate_agents_from_system_params(params):
    """
    Instancia al Sujeto (i) y al Sistema/Alter (j) basándose en el contexto
    específico de la interacción (Jefes, Equipos, Amigos, Pareja).
    """
    
    # Biblioteca de Sistemas y Arquetipos Organizacionales/Sociales
    SISTEMAS_ARQUETIPOS = {
        "PROFESSIONAL": {
            "BOSS_MICROMANAGER": { # Alta ansiedad de control, delay cero, hipervigilante
                "w_s": 0.10, "w_a": 0.70, "w_e": 0.05, "w_d": 0.15, 
                "G": 0.2, "A": 0.6, "P_default": 0.90
            },
            "COLLEAGUE_AVOIDANT": { # El clásico dev que se pierde, no responde Slack, pospone
                "w_s": 0.20, "w_a": 0.05, "w_e": 0.65, "w_d": 0.10, 
                "G": 0.3, "A": 0.0, "P_default": 0.60
            },
            "TEAM_CHAOTIC_AGILE": { # Alta entropía basal (ruido del entorno organizativo)
                "w_s": 0.15, "w_a": 0.35, "w_e": 0.10, "w_d": 0.40, 
                "G": 0.4, "A": 0.1, "P_default": 0.50
            }
        },
        "SOCIAL": {
            "FRIEND_DISTANT": {
                "w_s": 0.40, "w_a": 0.05, "w_e": 0.45, "w_d": 0.10, 
                "G": 0.4, "A": 0.2, "P_default": 0.70
            },
            "GROUP_PEER_PRESSURE": {
                "w_s": 0.20, "w_a": 0.50, "w_e": 0.10, "w_d": 0.20, 
                "G": 0.5, "A": -0.3, "P_default": 0.80
            }
        },
        "ROMANTIC": {
            "PARTNER_SECURE": {"w_s": 0.65, "w_a": 0.15, "w_e": 0.10, "w_d": 0.10, "G": 0.6, "A": 0.4, "P_default": 0.80},
            "PARTNER_AVOIDANT": {"w_s": 0.25, "w_a": 0.10, "w_e": 0.55, "w_d": 0.10, "G": 0.3, "A": 0.1, "P_default": 0.65},
            "PARTNER_ANXIOUS": {"w_s": 0.20, "w_a": 0.55, "w_e": 0.15, "w_d": 0.10, "G": 0.4, "A": -0.2, "P_default": 0.60}
        }
    }
    
    # 1. Instanciar Sujeto i (Ego)
    prof_i = params["_derived_agent_profile"]
    agent_i = Agent(
        w_s=prof_i["w_s"], w_a=prof_i["w_a"], w_e=prof_i["w_e"], w_d=prof_i["w_d"],
        G=prof_i.get("G", 0.5), A=prof_i["A"], P=prof_i["P_default"]
    )
    
    # 2. Instanciar Sistema/Alter j
    alter_cfg = params["_alter_settings"]
    print(str(alter_cfg))
    ctx = alter_cfg["context_type"]
    arch = alter_cfg["archetype"]
    
    if alter_cfg["custom_profile"] is not None:
        prof_j = alter_cfg["custom_profile"]
    else:
        # Buscamos en la matriz anidada; si no existe, cae en un perfil genérico neutro
        prof_j = SISTEMAS_ARQUETIPOS.get(ctx, {}).get(arch, {
            "w_s": 0.40, "w_a": 0.20, "w_e": 0.20, "w_d": 0.20, "G": 0.4, "A": 0.0, "P_default": 0.70
        })
        
    agent_j = Agent(
        w_s=prof_j["w_s"], w_a=prof_j["w_a"], w_e=prof_j["w_e"], w_d=prof_j["w_d"],
        G=prof_j.get("G", 0.5), A=prof_j["A"], P=prof_j["P_default"]
    )
    
    return agent_i, agent_j


def simular(params):

    params['noise_sigma'] = 0.05

    sujeto_i, compañero_j = generate_agents_from_system_params(params)

    # ============================================================
    # SIMULACIÓN
    # ============================================================

    sim = RAEEMSimulation(
        sujeto_i,
        compañero_j,
        params
    )

    ticks = 500

    history = {
        "H_i": [],
        "H_j": [],
        "I_i": [],
        "I_j": [],
        "C_i": [],
        "C_j": [],
    }

    for _ in range(ticks):

        state = sim.step()

        for k in history:
            history[k].append(state[k])

    # ============================================================
    # LLAMADA AUTOMÁTICA AL ANALIZADOR POST-SIMULACIÓN
    # ============================================================
    import json
    from analitica import compute_phenotype_signature

    print("\n==============================================")
    print("     RA-EEM PHENOTYPE SIGNATURE ENGINE")
    print("==============================================")

    # Generamos la firma computada pasándole el historial y tus hiperparámetros
    phenotype_json = compute_phenotype_signature(history, params)

    # Imprimimos el objeto formateado elegantemente en consola
    print(json.dumps(phenotype_json, indent=4))
    print("==============================================\n")


    # ============================================================
    # PLOTTING
    # ============================================================

    fig = plt.figure(figsize=(14, 10))

    # ------------------------------------------------------------
    # Conducta
    # ------------------------------------------------------------

    ax1 = plt.subplot(2, 2, 1)

    ax1.plot(history["H_i"], label="Ansioso")
    ax1.plot(history["H_j"], label="Evitativo")

    ax1.axhline(0, linestyle="--", alpha=0.4)

    ax1.set_title("Emisión Conductual")
    ax1.set_xlabel("Ticks")
    ax1.set_ylabel("H")
    ax1.legend()

    # ------------------------------------------------------------
    # Burnout
    # ------------------------------------------------------------

    ax2 = plt.subplot(2, 2, 2)

    ax2.plot(history["C_i"], label="Burnout Ansioso")
    ax2.plot(history["C_j"], label="Burnout Evitativo")

    ax2.plot(history["I_i"], alpha=0.5, label="Angustia Ansioso")
    ax2.plot(history["I_j"], alpha=0.5, label="Angustia Evitativo")

    ax2.set_title("Carga Energética")
    ax2.set_xlabel("Ticks")
    ax2.set_ylabel("[0,1]")

    ax2.legend()

    # ------------------------------------------------------------
    # Retrato de fase
    # ------------------------------------------------------------

    ax3 = plt.subplot(2, 1, 2)

    colors = np.arange(ticks)

    sc = ax3.scatter(
        history["H_i"],
        history["H_j"],
        c=colors,
        cmap="plasma",
        s=30
    )

    ax3.plot(
        history["H_i"],
        history["H_j"],
        alpha=0.4
    )

    ax3.scatter(
        history["H_i"][0],
        history["H_j"][0],
        s=120,
        color="green",
        label="Inicio"
    )

    ax3.scatter(
        history["H_i"][-1],
        history["H_j"][-1],
        s=120,
        color="red",
        label="Fin"
    )

    ax3.axhline(0, linestyle="--", alpha=0.3)
    ax3.axvline(0, linestyle="--", alpha=0.3)

    ax3.set_xlabel("H Ansioso")
    ax3.set_ylabel("H Evitativo")

    ax3.set_title("Retrato de Fase Relacional")

    ax3.legend()

    plt.colorbar(
        sc,
        ax=ax3,
        label="Tiempo"
    )

    plt.tight_layout()
    plt.show()