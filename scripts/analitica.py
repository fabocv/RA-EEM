import json
import numpy as np

# ============================================================
# MOTOR DE EXTRACCIÓN FENOMENOLÓGICA (RA-EEM ANALYTICS)
# ============================================================

def compute_phenotype_signature(history, params):
    """
    Analiza las series temporales de la simulación y genera una firma
    fenotípica basada en atractores, carga alostática y acoplamiento predictivo.
    """
    # --- Helpers Internos ---
    def safe_mean(arr): return float(np.mean(arr)) if len(arr) > 0 else 0.0
    def safe_std(arr): return float(np.std(arr)) if len(arr) > 0 else 0.0
    
    def slope(arr):
        if len(arr) < 2: return 0.0
        x = np.arange(len(arr))
        coeffs = np.polyfit(x, arr, 1)
        return float(coeffs[0])

    def bounded_label(value, ranges):
        for threshold, label in ranges:
            if value <= threshold:
                return label
        return ranges[-1][1]

    def phase_entropy(x, y, bins=20):
        if len(x) == 0 or len(y) == 0: return 0.0
        H, _, _ = np.histogram2d(x, y, bins=bins)
        P = H / np.sum(H)
        P = P[P > 0]
        entropy = -np.sum(P * np.log2(P))
        max_entropy = np.log2(bins * bins)
        return float(entropy / max_entropy)

    def estimate_oscillation(signal):
        if len(signal) == 0: return 0
        centered = signal - np.mean(signal)
        zero_crossings = np.where(np.diff(np.sign(centered)))[0]
        return len(zero_crossings)

    def estimate_repair_events(signal, threshold=0.15):
        if len(signal) < 2: return 0
        diffs = np.diff(signal)
        spikes = np.where(diffs > threshold)[0]
        return int(len(spikes))

    def calculate_lagged_correlation(x, y, lag):
        if lag <= 0 or lag >= len(x) or len(x) < 10:
            return float(np.corrcoef(x, y)[0, 1]) if len(x) > 1 else 0.0
        x_trunc = x[:-lag]
        y_trunc = y[lag:]
        corr = np.corrcoef(x_trunc, y_trunc)[0, 1]
        return float(corr) if not np.isnan(corr) else 0.0

    def detect_critical_velocity(signal, window=10):
        if len(signal) < 2: return 0.0
        diffs = np.diff(signal)
        if len(diffs) == 0: return 0.0
        window = min(window, len(diffs))
        moving_max = max([np.sum(diffs[i:i+window]) for i in range(len(diffs)-window+1)])
        return float(moving_max)

    # --- Extracción de Métricas Crudas ---
    metrics = {}
    tau_delay = params.get("tau", 10)
    repair_str = params.get("repair_strength", 0.15)

    metrics["mean_H_i"] = safe_mean(history["H_i"])
    metrics["mean_H_j"] = safe_mean(history["H_j"])
    metrics["std_H_i"] = safe_std(history["H_i"])
    metrics["std_H_j"] = safe_std(history["H_j"])
    metrics["oscillations_i"] = estimate_oscillation(np.array(history["H_i"]))
    metrics["oscillations_j"] = estimate_oscillation(np.array(history["H_j"]))

    metrics["lagged_resonance_ij"] = calculate_lagged_correlation(
        np.array(history["H_i"]), np.array(history["H_j"]), lag=tau_delay
    )

    metrics["peak_I_i"] = float(np.max(history["I_i"])) if len(history["I_i"]) > 0 else 0.0
    metrics["peak_I_j"] = float(np.max(history["I_j"])) if len(history["I_j"]) > 0 else 0.0
    metrics["mean_I_i"] = safe_mean(history["I_i"])
    metrics["mean_I_j"] = safe_mean(history["I_j"])
    metrics["angst_acceleration_i"] = detect_critical_velocity(history["I_i"])

    metrics["max_C_i"] = float(np.max(history["C_i"])) if len(history["C_i"]) > 0 else 0.0
    metrics["max_C_j"] = float(np.max(history["C_j"])) if len(history["C_j"]) > 0 else 0.0
    metrics["mean_C_i"] = safe_mean(history["C_i"])
    metrics["mean_C_j"] = safe_mean(history["C_j"])

    metrics["phase_entropy"] = phase_entropy(np.array(history["H_i"]), np.array(history["H_j"]))
    metrics["repair_events_j"] = estimate_repair_events(np.array(history["H_j"]), threshold=repair_str)

    # --- Clasificación de Perfiles ---
    signature = {}

    signature["regulation_profile"] = {
        "stress_tolerance": bounded_label(metrics["peak_I_i"], [(0.15, "high"), (0.35, "moderate"), (1.0, "low")]),
        "burnout_resistance": bounded_label(max(metrics["max_C_i"], metrics["max_C_j"]), [(0.10, "very_high"), (0.30, "high"), (0.60, "moderate"), (1.00, "fragile")]),
        "emotional_variability": bounded_label(metrics["std_H_i"], [(0.05, "stable"), (0.15, "dynamic"), (1.0, "chaotic")]),
        "shock_absorption": bounded_label(metrics["angst_acceleration_i"], [(0.05, "gradual_adaptation"), (0.20, "acute_impact"), (1.0, "explosive_shattering")])
    }

    derived = params.get("_derived_agent_profile", {})
    p_def = derived.get("P_default", 0.8)
    signature["predictive_profile"] = {
        "threat_bias": bounded_label(params["chi"] / params["kappa"], [(0.8, "positive_bias"), (1.2, "balanced"), (2.0, "threat_sensitive"), (10.0, "hypervigilant")]),
        "prediction_rigidity": bounded_label(p_def, [(0.4, "flexible"), (0.7, "moderate"), (1.0, "rigid")]),
        "delay_processing": bounded_label(params["tau"], [(5, "fast"), (15, "moderate"), (30, "deep_processing")])
    }

    # Taxonomía del Atractor Relacional
    m_i, m_j = metrics["mean_H_i"], metrics["mean_H_j"]
    if m_i > 0.15 and m_j > 0.15:
        attractor = "mutual_prosocial_resonance"
    elif m_i < -0.15 and m_j < -0.15:
        attractor = "mutual_hostile_collapse"
    elif m_i > 0.15 and m_j < -0.15:
        attractor = "polarized_pursuit_evasive"
    elif m_i < -0.15 and m_j > 0.15:
        attractor = "inverse_polarized_rebellion"
    else:
        attractor = "stochastic_drift_neutral"

    signature["relational_stability"] = {
        "attractor_type": attractor,
        "phase_structure": bounded_label(metrics["phase_entropy"], [(0.2, "fixed_point"), (0.5, "bounded_orbit"), (0.8, "complex_dynamic"), (1.0, "chaotic")]),
        "predictive_attunement": bounded_label(metrics["lagged_resonance_ij"], [(-0.2, "counter_regulated"), (0.2, "uncoupled"), (0.6, "synchronized"), (1.0, "hyper_resonant")]),
        "repair_capacity": bounded_label(metrics["repair_events_j"], [(1, "minimal"), (5, "intermittent"), (20, "active"), (1000, "hyperactive")])
    }

    signature["energetic_profile"] = {
        "allostatic_load": bounded_label((metrics["mean_C_i"] + metrics["mean_C_j"]) / 2, [(0.05, "minimal"), (0.20, "moderate"), (0.50, "high"), (1.00, "critical")]),
        "noise_tolerance": bounded_label(params["noise_sigma"], [(0.03, "low_noise"), (0.08, "realistic_dynamic"), (0.15, "high_noise"), (1.0, "chaotic_environment")])
    }

    # --- Patrones Emergentes Sistémicos ---
    patterns = []
    if metrics["max_C_i"] < 0.1 and metrics["max_C_j"] < 0.1: patterns.append("burnout_resilient_homeostasis")
    if attractor == "mutual_prosocial_resonance" and metrics["lagged_resonance_ij"] > 0.4: patterns.append("co_regulatory_attunement")
    if attractor == "polarized_pursuit_evasive": patterns.append("chronic_asymmetric_loop")
    if metrics["phase_entropy"] > 0.3 and metrics["phase_entropy"] < 0.7 and params["noise_sigma"] >= 0.05: patterns.append("bounded_stochastic_orbit")
    if metrics["angst_acceleration_i"] > 0.15 and metrics["max_C_i"] > 0.5: patterns.append("brittle_system_shattering")
    if params["tau"] > 15: patterns.append("slow_predictive_processing")

    signature["emergent_patterns"] = patterns
    signature["simulation_statistics"] = metrics

    return signature