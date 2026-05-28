import sys
import os

sys.path.append(
    os.path.abspath("..")
)

from simulador_api import simular_api
test_params = {
    "lambda_s": 1.191,
    "lambda_r": 0.256,
    "lambda_g": 0.12,
    "lambda_I": 0.05,
    "sigma": 1.0,
    "kappa": 0.96,
    "chi": 1.175,
    "alpha": 0.0076,
    "eta_symp": 0.0009,
    "eta_evit": 0.0007,
    "beta": 0.0156,
    "p_burnout": 1.5,
    "q_fatigue": 3,
    "alpha_a": 0.02,
    "alpha_e": 0.01,
    "gamma_plus": 0.0124,
    "gamma_minus": 0.0158,
    "nu": 0.08,
    "mu_a": 0.2,
    "delta_a": 0.08,
    "mu_e": 0.1,
    "delta_e": 0.05,
    "tau": 5,
    "rho_e": 0.04,
    "repair_threshold": 0.761,
    "repair_probability": 0.033,
    "repair_strength": 0.8,
    "zeta": 0.008,
    "noise_sigma": 0.017,
    "_derived_agent_profile": {
        "w_s": 0.391,
        "w_a": 0.203,
        "w_e": 0.305,
        "w_d": 0.102,
        "A": -0.844,
        "P_default": 0.439
    },
    "_stress_profile": "LOW_NOISE_STABLE",
    "_alter_settings": {
        "context_type": "FAMILIAL",
        "archetype": "EMOTIONALLY_ABSENT",
        "custom_profile": {
            "w_s": 0.7,
            "w_a": 0.8,
            "w_e": 0.76,
            "w_d": 0.3,
            "G": 0.55,
            "A": 0.8,
            "P_default": 0.7
        }
    }
}
_test_params = {
    'lambda_s': 1.181, 'lambda_r': 0.6, 'lambda_g': 0.35, 'lambda_I': 0.05,
    'sigma': 1.0, 'kappa': 2.2, 'chi': 2.5, 'alpha': 0.029,
    'eta_symp': 0.0045, 'eta_evit': 0.003, 'beta': 0.066,
    'p_burnout': 1.5, 'q_fatigue': 3, 'alpha_a': 0.02, 'alpha_e': 0.01,
    'gamma_plus': 0.031, 'gamma_minus': 0.04, 'nu': 0.08,
    'mu_a': 0.2, 'delta_a': 0.08, 'mu_e': 0.1, 'delta_e': 0.05,
    'tau': 17, 'rho_e': 0.04, 'repair_threshold': 0.44,
    'repair_probability': 0.12, 'repair_strength': 0.8,
    'zeta': 0.045, 'noise_sigma': 0.061,
    '_derived_agent_profile': {
        'w_s': 0.381, 'w_a': 0.238, 'w_e': 0.286, 'w_d': 0.095,
        'A': 0.4, 'P_default': 0.785
    },
    '_alter_settings': {
        'context_type': 'FAMILIAL',
        'archetype': 'EMOTIONALLY_ABSENT',
        'custom_profile': {
            'w_s': 0.65, 'w_a': 0.8, 'w_e': 0.7, 'w_d': 0.4,
            'G': 0.5, 'A': 0.7, 'P_default': 0.75
        }
    }
}

result = simular_api(test_params)
print('✅ Simulación OK')
print('Atractor:', result['phenotype']['relational_stability']['attractor_type'])
print('Patrones:', result['phenotype']['emergent_patterns'])
print('Imagen generada:', result['image_base64'][:50] + '...')