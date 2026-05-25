from cuestionario import RAEEMQuestionnaire
from simulador import simular

_params = {
    "lambda_s": 1.181,
    "lambda_r": 0.6,
    "lambda_g": 0.35,
    "lambda_I": 0.05,
    "sigma": 1.0,
    "kappa": 2.2,
    "chi": 2.5,
    "alpha": 0.029,
    "eta_symp": 0.0045,
    "eta_evit": 0.003,
    "beta": 0.066,
    "p_burnout": 1.5,
    "q_fatigue": 3,
    "alpha_a": 0.02,
    "alpha_e": 0.01,
    "gamma_plus": 0.031,
    "gamma_minus": 0.04,
    "nu": 0.08,
    "mu_a": 0.2,
    "delta_a": 0.08,
    "mu_e": 0.1,
    "delta_e": 0.05,
    "tau": 17,
    "rho_e": 0.04,
    "repair_threshold": 0.44,
    "repair_probability": 0.12,
    "repair_strength": 0.8,
    "zeta": 0.045,
    "noise_sigma": 0.061,
    "_derived_agent_profile": {
        "w_s": 0.381,
        "w_a": 0.238,
        "w_e": 0.286,
        "w_d": 0.095,
        "A": 0.4,
        "P_default": 0.785
    },
    "_stress_profile": "REALISTIC_DYNAMIC"
}

if __name__ == "__main__":
    default = int(input("desea usar valores por defecto [test]? 1: si, 0: no, quiero correr el cuestionario desde cero. > "))
    params = _params
    if (default == 0):
        q = RAEEMQuestionnaire()
        params = q.run()

    simular(params=params)

