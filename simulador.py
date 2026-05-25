# ============================================================
# RA-EEM v0.3.3
# Simulación Completa + Gráficas
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

    def emit_behavior(self, ag, perceived_partner_distress):

        p = self.p

        repair_boost = 0.0

        # Reparación intermitente
        if (
            ag.w_e > 0.45
            and perceived_partner_distress > p["repair_threshold"]
            and np.random.rand() < p["repair_probability"]
        ):

            repair_boost = p["repair_strength"]

        raw = (
            (
                p["lambda_s"] * ag.w_s
                + p["lambda_r"] * ag.R
                + p["lambda_g"] * ag.G
                + repair_boost
            )
            * (1.0 - ag.C)
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

        # ----------------------------------------------------
        # Activación evitativa
        # ----------------------------------------------------

        self.i.w_tilde_e += (
            p["mu_e"]
            * self.i.I
            -
            p["delta_e"]
            * (
                self.i.w_tilde_e
                - self.i.w_e
            )
        )

        self.j.w_tilde_e += (
            p["mu_e"]
            * self.j.I
            -
            p["delta_e"]
            * (
                self.j.w_tilde_e
                - self.j.w_e
            )
        )

        # ----------------------------------------------------
        # Emisión conductual
        # ----------------------------------------------------

        self.H_i = self.emit_behavior(
            self.i,
            self.j.I
        )

        self.H_j = self.emit_behavior(
            self.j,
            self.i.I
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
            self.i.I + delta_I_i,
            0.0,
            1.0
        )

        self.j.I = np.clip(
            self.j.I + delta_I_j,
            0.0,
            1.0
        )

        # ----------------------------------------------------
        # Burnout
        # ----------------------------------------------------

        delta_C_i = (
            p["alpha"]
            * self.i.I
            -
            p["beta"]
            * (
                (1.0 - self.i.C)
                ** p["p_burnout"]
            )
            * self.i.w_s
            -
            p["zeta"]
            * max(0.0, self.H_j)
        )

        delta_C_j = (
            p["alpha"]
            * self.j.I
            -
            p["beta"]
            * (
                (1.0 - self.j.C)
                ** p["p_burnout"]
            )
            * self.j.w_s
            -
            p["zeta"]
            * max(0.0, self.H_i)
        )

        self.i.C = np.clip(
            self.i.C + delta_C_i,
            0.0,
            1.0
        )

        self.j.C = np.clip(
            self.j.C + delta_C_j,
            0.0,
            1.0
        )

        # ----------------------------------------------------
        # Memoria relacional
        # ----------------------------------------------------

        self.i.M += (
            p["gamma_plus"]
            * max(0.0, self.H_j)
            * (1.0 - self.i.M)
            +
            p["gamma_minus"]
            * min(0.0, self.H_j)
            * (1.0 + self.i.M)
        )

        self.j.M += (
            p["gamma_plus"]
            * max(0.0, self.H_i)
            * (1.0 - self.j.M)
            +
            p["gamma_minus"]
            * min(0.0, self.H_i)
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


# ============================================================
# PARÁMETROS
# ============================================================

params = {

    "lambda_s": 1.2,
    "lambda_r": 0.5,
    "lambda_g": 0.3,

    "sigma": 1.0,

    "kappa": 1.6,
    "chi": 2.2,

    "alpha": 0.04,
    "beta": 0.12,
    "p_burnout": 1.5,

    "gamma_plus": 0.015,
    "gamma_minus": 0.04,

    "nu": 0.08,

    "mu_a": 0.2,
    "delta_a": 0.08,

    "mu_e": 0.1,
    "delta_e": 0.05,

    "tau": 10,

    "repair_threshold": 0.6,
    "repair_probability": 0.12,
    "repair_strength": 0.8,

    "zeta": 0.03,

    "noise_sigma": 0.015,
}


# ============================================================
# AGENTES
# ============================================================

ansioso = Agent(
    w_s=0.25,
    w_a=0.65,
    w_e=0.05,
    w_d=0.05,
    G=0.7,
    A=0.1,
)

evitativo = Agent(
    w_s=0.20,
    w_a=0.10,
    w_e=0.65,
    w_d=0.05,
    G=0.2,
    A=0.5,
)

# ============================================================
# SIMULACIÓN
# ============================================================

sim = RAEEMSimulation(
    ansioso,
    evitativo,
    params
)

ticks = 160

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