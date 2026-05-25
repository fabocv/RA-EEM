# ============================================================
# RA-EEM PARAMETER QUESTIONNAIRE v0.3.0
# ------------------------------------------------------------
# Objetivo:
#   Inferir hiperparámetros dinámicos del modelo RA-EEM
#   mediante un cuestionario validado interactivo.
#
# Incluye:
#   - Perfil de apego
#   - Regulación emocional
#   - Burnout / fatiga
#   - Co-regulación
#   - Sesgo perceptivo
#   - Entorno / ruido sistémico
#   - Delay relacional
#   - Estimación automática de parámetros
#
# Output:
#   params = {...}
#
# ============================================================

import json


# ============================================================
# HELPERS
# ============================================================

def ask_scale(question, minimum=0, maximum=10):

    while True:

        try:

            print(f"\n{question}")
            value = float(input(f"[{minimum}-{maximum}] > "))

            if minimum <= value <= maximum:
                return value

            print("Valor fuera de rango.")

        except ValueError:
            print("Ingresa un número válido.")


def normalize(x, scale=10.0):

    return x / scale


def clamp(x, a, b):

    return max(a, min(x, b))

def ask_choice(prompt, options):

    while True:

        print(f"\n{prompt}")

        for k, v in options.items():
            print(f"  [{k}] {v}")

        value = input("> ").strip()

        if value in options:
            return options[value]

        print("❌ Opción inválida.")


def ask_float(prompt, min_v=0.0, max_v=1.0):

    while True:

        try:

            v = float(input(f"{prompt} ({min_v}-{max_v}): "))

            if min_v <= v <= max_v:
                return round(v, 3)

        except:
            pass

        print("❌ Valor inválido.")

# ============================================================
# CONTEXTO DEL ALTER (OTRO AGENTE)
# ============================================================

ALTER_CONTEXTS = {
    "1": "ROMANTIC",
    "2": "PROFESSIONAL",
    "3": "SOCIAL",
    "4": "FAMILIAL",
}

ALTER_ARCHETYPES = {

    "ROMANTIC": {
        "1": "SECURE_PARTNER",
        "2": "ANXIOUS_PURSUER",
        "3": "AVOIDANT_WITHDRAWER",
        "4": "DISORGANIZED_PARTNER",
        "5": "HOT_COLD_DYNAMIC",
        "6": "EMOTIONALLY_UNAVAILABLE",
    },

    "PROFESSIONAL": {
        "1": "COLLABORATIVE_PEER",
        "2": "BOSS_MICROMANAGER",
        "3": "EMOTIONALLY_DETACHED_MANAGER",
        "4": "HIGH_PRESSURE_SUPERVISOR",
        "5": "UNPREDICTABLE_AUTHORITY",
        "6": "PASSIVE_AGGRESSIVE_COWORKER",
    },

    "SOCIAL": {
        "1": "SUPPORTIVE_FRIEND",
        "2": "INCONSISTENT_FRIEND",
        "3": "SOCIAL_AVOIDANT",
        "4": "DOMINANT_PERSONALITY",
        "5": "VALIDATING_COMPANION",
        "6": "CHAOTIC_SOCIAL_NODE",
    },

    "FAMILIAL": {
        "1": "SECURE_ATTACHMENT_FIGURE",
        "2": "CRITICAL_PARENT",
        "3": "EMOTIONALLY_ABSENT",
        "4": "OVERPROTECTIVE_FIGURE",
        "5": "UNPREDICTABLE_CAREGIVER",
        "6": "FUSED_BOUNDARY_DYNAMIC",
    }
}


# ============================================================
# QUESTIONNAIRE
# ============================================================

class RAEEMQuestionnaire:

    def __init__(self):

        self.answers = {}

    # ========================================================
    # APEGO
    # ========================================================

    def attachment_block(self):

        print("\n================================================")
        print("PERFIL DE APEGO")
        print("================================================")

        self.answers["security"] = ask_scale(
            "¿Qué tan fácil te resulta sentir estabilidad emocional "
            "incluso cuando la relación atraviesa tensión?"
        )

        self.answers["anxiety"] = ask_scale(
            "¿Qué tan intensamente temes abandono, distancia "
            "o pérdida emocional?"
        )

        self.answers["avoidance"] = ask_scale(
            "¿Qué tan frecuentemente necesitas distancia emocional "
            "o te cierras cuando algo duele?"
        )

        self.answers["disorganization"] = ask_scale(
            "¿Sientes impulsos contradictorios simultáneos "
            "(buscar cercanía y rechazarla al mismo tiempo)?"
        )


    def alter_block(self):
            # ============================================================
        # CUESTIONARIO ALTER
        # ============================================================

        print("\n================================================")
        print("     CONFIGURACIÓN DEL OTRO AGENTE (ALTER)")
        print("================================================")

        context_type = ask_choice(
            "¿Qué rol tiene el otro agente en tu vida?",
            {
                "1": "ROMANTIC",
                "2": "PROFESSIONAL",
                "3": "SOCIAL",
                "4": "FAMILIAL",
            }
        )

        archetype = ask_choice(
            f"¿Qué arquetipo describe mejor al otro agente ({context_type})?",
            ALTER_ARCHETYPES[context_type]
        )

        use_custom = ask_choice(
            "¿Deseas definir manualmente rasgos del otro agente?",
            {
                "1": "YES",
                "2": "NO",
            }
        )

        custom_profile = None

        if use_custom == "YES":

            print("\n--- Perfil Personalizado del Alter ---")

            custom_profile = {

                "w_s": ask_float(
                    "Seguridad basal del alter",
                    0.0,
                    1.0
                ),

                "w_a": ask_float(
                    "Ansiedad basal del alter",
                    0.0,
                    1.0
                ),

                "w_e": ask_float(
                    "Evitación basal del alter",
                    0.0,
                    1.0
                ),

                "w_d": ask_float(
                    "Desorganización basal del alter",
                    0.0,
                    1.0
                ),

                "G": ask_float(
                    "Empatía del alter",
                    0.0,
                    1.0
                ),

                "A": ask_float(
                    "Agencia/autonomía del alter",
                    0.0,
                    1.0
                ),

                "P_default": ask_float(
                    "¿Qué tan firmemente el alter confía en su interpretación emocional de las relaciones?",
                    0.0,
                    1.0
                ),
            }

        self.answers["_alter_settings"] = {
            "context_type": context_type,
            "archetype":archetype,
            "custom_profile": custom_profile
        }

    # ========================================================
    # REGULACIÓN
    # ========================================================

    def regulation_block(self):

        print("\n================================================")
        print("REGULACIÓN Y FUNCIONAMIENTO EJECUTIVO")
        print("================================================")

        self.answers["masking"] = ask_scale(
            "¿Qué tan capaz eres de mantener una conducta funcional "
            "aunque estés emocionalmente mal?"
        )

        self.answers["empathy"] = ask_scale(
            "¿Qué tan responsable te sientes por regular "
            "o contener emocionalmente al otro?"
        )

        self.answers["agency"] = ask_scale(
            "¿Qué tanta autonomía real tienes dentro "
            "de la relación o sistema?"
        )

    

    # ========================================================
    # BURNOUT
    # ========================================================

    def burnout_block(self):

        print("\n================================================")
        print("FATIGA Y CARGA ALOSTÁTICA")
        print("================================================")

        self.answers["burnout_speed"] = ask_scale(
            "¿Qué tan rápido sientes agotamiento emocional "
            "cuando hay conflicto o estrés relacional?"
        )

        self.answers["recovery_speed"] = ask_scale(
            "¿Qué tan rápido recuperas energía emocional "
            "después de tensión?"
        )

        self.answers["hyperactivation_cost"] = ask_scale(
            "¿Cuánto desgaste produce permanecer "
            "emocionalmente hiperactivado?"
        )

        self.answers["avoidant_cost"] = ask_scale(
            "¿Cuánto desgaste produce sostener distancia emocional "
            "o reprimir necesidades?"
        )

    # ========================================================
    # MEMORIA Y FILTROS
    # ========================================================

    def perception_block(self):

        print("\n================================================")
        print("PERCEPCIÓN Y FILTROS PREDICTIVOS")
        print("================================================")

        self.answers["threat_bias"] = ask_scale(
            "¿Qué tan fácil interpretas ambigüedad "
            "como rechazo, crítica o abandono?"
        )

        self.answers["repair_visibility"] = ask_scale(
            "Cuando alguien intenta reparar o acercarse, "
            "¿qué tan fácil puedes percibirlo como genuino?"
        )

        self.answers["hypervigilance"] = ask_scale(
            "¿Qué tan atento/a estás a micro-cambios "
            "emocionales del otro?"
        )

        self.answers["memory_negativity"] = ask_scale(
            "¿Las experiencias negativas pesan más "
            "que las positivas en tu memoria relacional?"
        )

    # ========================================================
    # AMBIENTE
    # ========================================================

    def environment_block(self):

        print("\n================================================")
        print("CONTEXTO AMBIENTAL Y ENTROPÍA RELACIONAL")
        print("================================================")

        self.answers["env_instability"] = ask_scale(
            "¿Qué tan impredecible es el entorno externo "
            "(dinero, trabajo, salud, familia, tiempo)?"
        )

        self.answers["conflict_noise"] = ask_scale(
            "¿Qué tanta fricción cotidiana aparece "
            "aunque nadie quiera pelear?"
        )

        self.answers["communication_delay"] = ask_scale(
            "¿Qué tan frecuentes son silencios, retrasos "
            "o desincronizaciones comunicacionales?"
        )

        self.answers["async_latency"] = ask_scale(
            "¿Cuánto tarda normalmente una reparación "
            "o reconexión emocional?"
        )

    # ========================================================
    # CO-REGULACIÓN
    # ========================================================

    def coregulation_block(self):

        print("\n================================================")
        print("CO-REGULACIÓN Y REPARACIÓN")
        print("================================================")

        self.answers["coregulation"] = ask_scale(
            "¿Sentir apoyo o cercanía del otro "
            "reduce realmente tu estrés?"
        )

        self.answers["repair_speed"] = ask_scale(
            "¿Qué tan rápido intentas reparar "
            "después de tensión o conflicto?"
        )

        self.answers["repair_probability"] = ask_scale(
            "¿Qué tan probable es que hagas esfuerzos "
            "de acercamiento incluso estando agotado/a?"
        )

    # ========================================================
    # PARAM COMPUTATION
    # ========================================================

    def compute_params(self):

        a = self.answers

        # ----------------------------------------------------
        # Apego
        # ----------------------------------------------------

        w_s = normalize(a["security"])
        w_a = normalize(a["anxiety"])
        w_e = normalize(a["avoidance"])
        w_d = normalize(a["disorganization"])

        # Normalización distributiva
        total = w_s + w_a + w_e + w_d

        w_s /= total
        w_a /= total
        w_e /= total
        w_d /= total

        # ----------------------------------------------------
        # Regulación
        # ----------------------------------------------------

        lambda_r = 0.2 + normalize(a["masking"]) * 0.8
        lambda_g = 0.1 + normalize(a["empathy"]) * 0.5

        # Agencia estructural
        A = (normalize(a["agency"]) * 2.0) - 1.0

        # ----------------------------------------------------
        # Burnout
        # ----------------------------------------------------

        alpha = 0.005 + normalize(a["burnout_speed"]) * 0.04

        beta = (
            0.01
            + normalize(a["recovery_speed"]) * 0.08
        )

        eta_symp = (
            0.0005
            + normalize(a["hyperactivation_cost"]) * 0.005
        )

        eta_evit = (
            0.0005
            + normalize(a["avoidant_cost"]) * 0.005
        )

        # ----------------------------------------------------
        # Filtros perceptivos
        # ----------------------------------------------------

        chi = 1.0 + normalize(a["threat_bias"]) * 2.5

        kappa = 0.8 + normalize(a["repair_visibility"]) * 2.0

        P_default = (
            0.4
            + normalize(a["hypervigilance"]) * 0.55
        )

        gamma_minus = (
            0.015
            + normalize(a["memory_negativity"]) * 0.05
        )

        gamma_plus = (
            0.01
            + normalize(a["repair_visibility"]) * 0.03
        )

        # ----------------------------------------------------
        # Entorno / ruido
        # ----------------------------------------------------

        environmental_noise = (
            a["env_instability"]
            + a["conflict_noise"]
            + a["communication_delay"]
        ) / 30.0

        noise_sigma = (
            0.01
            + environmental_noise * 0.14
        )

        noise_sigma = round(noise_sigma, 3)

        # ----------------------------------------------------
        # Delay temporal
        # ----------------------------------------------------

        tau = int(
            5
            + a["async_latency"] * 2.5
        )

        # ----------------------------------------------------
        # Co-regulación
        # ----------------------------------------------------

        zeta = (
            0.005
            + normalize(a["coregulation"]) * 0.05
        )

        repair_threshold = (
            0.8
            - normalize(a["repair_speed"]) * 0.6
        )

        repair_probability = (
            0.02
            + normalize(a["repair_probability"]) * 0.25
        )

        # ----------------------------------------------------
        # Stress profile
        # ----------------------------------------------------

        if noise_sigma < 0.03:

            stress_profile = "LOW_NOISE_STABLE"

        elif noise_sigma < 0.08:

            stress_profile = "REALISTIC_DYNAMIC"

        elif noise_sigma < 0.15:

            stress_profile = "HIGH_ENTROPY_EDGE"

        else:

            stress_profile = "CHAOTIC_COLLAPSE_RISK"

        # ----------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------

        params = {

            "lambda_s": round(0.8 + w_s, 3),
            "lambda_r": round(lambda_r, 3),
            "lambda_g": round(lambda_g, 3),
            "lambda_I": 0.05,

            "sigma": 1.0,

            "kappa": round(kappa, 3),
            "chi": round(chi, 3),

            "alpha": round(alpha, 4),

            "eta_symp": round(eta_symp, 4),
            "eta_evit": round(eta_evit, 4),

            "beta": round(beta, 4),

            "p_burnout": 1.5,

            "q_fatigue": 3,

            "alpha_a": 0.02,
            "alpha_e": 0.01,

            "gamma_plus": round(gamma_plus, 4),
            "gamma_minus": round(gamma_minus, 4),

            "nu": 0.08,

            "mu_a": 0.2,
            "delta_a": 0.08,

            "mu_e": 0.1,
            "delta_e": 0.05,

            "tau": tau,

            "rho_e": 0.04,

            "repair_threshold": round(repair_threshold, 3),

            "repair_probability": round(
                repair_probability,
                3
            ),

            "repair_strength": 0.8,

            "zeta": round(zeta, 4),

            "noise_sigma": noise_sigma,

            # --------------------------------------------
            # Perfil derivado del sujeto
            # --------------------------------------------

            "_derived_agent_profile": {

                "w_s": round(w_s, 3),
                "w_a": round(w_a, 3),
                "w_e": round(w_e, 3),
                "w_d": round(w_d, 3),

                "A": round(A, 3),
                "P_default": round(P_default, 3),

            },

            "_stress_profile": stress_profile,
        }

        params["_alter_settings"] = a["_alter_settings"]

        return params

    # ========================================================
    # RUN
    # ========================================================

    def run(self):

        print("\n")
        print("################################################")
        print("# RA-EEM PARAMETER QUESTIONNAIRE v0.3.1")
        print("################################################")

        self.alter_block()
        self.attachment_block()
        self.regulation_block()
        self.burnout_block()
        self.perception_block()
        self.environment_block()
        self.coregulation_block()

        params = self.compute_params()

        print("\n================================================")
        print("PARAMS GENERADOS")
        print("================================================\n")

        print("params = ")
        print(
            json.dumps(
                params,
                indent=4
            )
        )

        return params


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    q = RAEEMQuestionnaire()
    q.run()