# ============================================================
# RA-EEM — NIVEL 2
# GRAFO DE ACOPLAMIENTO DIÁDICO
# ============================================================

import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

from networkx.algorithms.community import (
    greedy_modularity_communities,
    modularity
)

# ============================================================
# VARIABLES DEL SISTEMA
# ============================================================

DEFAULT_VARIABLES = [

    # Agente i
    "H_i",
    "I_i",
    "C_i",
    "M_i",
    "E_i",
    "wa_i",
    "we_i",

    # Agente j
    "H_j",
    "I_j",
    "C_j",
    "M_j",
    "E_j",
    "wa_j",
    "we_j",
]

# ============================================================
# MATRIZ DE CORRELACIÓN
# ============================================================

def build_correlation_matrix(
    history,
    variables=None
):

    if variables is None:
        variables = DEFAULT_VARIABLES

    data = np.array([
        history[v]
        for v in variables
    ])

    corr = np.corrcoef(data)

    return corr, variables


# ============================================================
# GRAFO FUNCIONAL
# ============================================================

def build_dyadic_graph(
    history,
    theta=0.3,
    variables=None
):

    if variables is None:
        variables = DEFAULT_VARIABLES

    corr, variables = build_correlation_matrix(
        history,
        variables
    )

    G = nx.Graph()

    # ========================================================
    # NODOS
    # ========================================================

    for var in variables:

        agent = "i" if var.endswith("_i") else "j"

        G.add_node(
            var,
            agent=agent
        )

    # ========================================================
    # ENLACES
    # ========================================================

    for i in range(len(variables)):

        for j in range(i + 1, len(variables)):

            r = corr[i, j]

            if np.isnan(r):
                continue

            if abs(r) >= theta:

                G.add_edge(
                    variables[i],
                    variables[j],

                    weight=float(abs(r)),
                    signed_weight=float(r),

                    relation=(
                        "positive"
                        if r > 0
                        else "negative"
                    )
                )

    return G, corr


# ============================================================
# MODULARIDAD
# ============================================================

def compute_modularity(G):

    if len(G.edges()) == 0:

        return {
            "Q": np.nan,
            "communities": []
        }

    communities = list(
        greedy_modularity_communities(
            G,
            weight="weight"
        )
    )

    Q = modularity(
        G,
        communities,
        weight="weight"
    )

    return {
        "Q": float(Q),
        "communities": [
            list(c)
            for c in communities
        ]
    }


# ============================================================
# DENSIDAD INTER-AGENTE
# ============================================================

def compute_inter_density(G):

    nodes_i = [
        n for n in G.nodes
        if n.endswith("_i")
    ]

    nodes_j = [
        n for n in G.nodes
        if n.endswith("_j")
    ]

    inter_edges = 0

    for u, v in G.edges():

        cross = (
            (u.endswith("_i") and v.endswith("_j"))
            or
            (u.endswith("_j") and v.endswith("_i"))
        )

        if cross:
            inter_edges += 1

    possible_inter = len(nodes_i) * len(nodes_j)

    density = inter_edges / possible_inter

    return {
        "inter_edges": inter_edges,
        "possible_inter": possible_inter,
        "inter_density": float(density)
    }


# ============================================================
# DENSIDAD INTRA-AGENTE
# ============================================================

def compute_intra_density(G):

    intra_edges = 0

    for u, v in G.edges():

        same_agent = (
            (u.endswith("_i") and v.endswith("_i"))
            or
            (u.endswith("_j") and v.endswith("_j"))
        )

        if same_agent:
            intra_edges += 1

    n_i = len([
        n for n in G.nodes
        if n.endswith("_i")
    ])

    n_j = len([
        n for n in G.nodes
        if n.endswith("_j")
    ])

    possible_intra = (
        n_i*(n_i-1)/2
        +
        n_j*(n_j-1)/2
    )

    density = intra_edges / possible_intra

    return {
        "intra_edges": intra_edges,
        "possible_intra": possible_intra,
        "intra_density": float(density)
    }


# ============================================================
# ASYMMETRY INDEX
# ============================================================

def compute_asymmetry_index(G):

    degree_i = 0
    degree_j = 0

    for node, degree in G.degree():

        if node.endswith("_i"):
            degree_i += degree

        elif node.endswith("_j"):
            degree_j += degree

    eps = 1e-8

    AI = (
        abs(degree_i - degree_j)
        /
        (degree_i + degree_j + eps)
    )

    return {
        "degree_i": int(degree_i),
        "degree_j": int(degree_j),
        "asymmetry_index": float(AI)
    }


# ============================================================
# PIPELINE COMPLETO
# ============================================================

def analyze_dyadic_coupling(
    history,
    theta=0.3
):

    G, corr = build_dyadic_graph(
        history,
        theta=theta
    )

    modularity_metrics = compute_modularity(G)

    inter_metrics = compute_inter_density(G)

    intra_metrics = compute_intra_density(G)

    asymmetry_metrics = compute_asymmetry_index(G)

    results = {

        # ----------------------------------------------------
        # GRAFO
        # ----------------------------------------------------

        "graph": G,

        # ----------------------------------------------------
        # MATRIZ
        # ----------------------------------------------------

        "correlation_matrix": corr,

        # ----------------------------------------------------
        # MODULARIDAD
        # ----------------------------------------------------

        "Q": modularity_metrics["Q"],
        "communities": modularity_metrics["communities"],

        # ----------------------------------------------------
        # DENSIDADES
        # ----------------------------------------------------

        "inter_density":
            inter_metrics["inter_density"],

        "intra_density":
            intra_metrics["intra_density"],

        # ----------------------------------------------------
        # ASIMETRÍA
        # ----------------------------------------------------

        "asymmetry_index":
            asymmetry_metrics["asymmetry_index"],

        "degree_i":
            asymmetry_metrics["degree_i"],

        "degree_j":
            asymmetry_metrics["degree_j"],
    }

    return results


# ============================================================
# VISUALIZACIÓN
# ============================================================

def plot_dyadic_graph(
    G,
    title="RA-EEM Dyadic Coupling Graph"
):

    plt.figure(figsize=(12, 10))

    pos = nx.spring_layout(
        G,
        seed=42
    )

    node_colors = []

    for node in G.nodes():

        if node.endswith("_i"):
            node_colors.append("skyblue")
        else:
            node_colors.append("salmon")

    edge_colors = []

    for u, v, data in G.edges(data=True):

        if data["signed_weight"] > 0:
            edge_colors.append("green")
        else:
            edge_colors.append("red")

    edge_widths = [
        2 + 4*abs(data["signed_weight"])
        for _, _, data in G.edges(data=True)
    ]

    nx.draw_networkx_nodes(
        G,
        pos,
        node_color=node_colors,
        node_size=1200
    )

    nx.draw_networkx_labels(
        G,
        pos,
        font_size=10
    )

    nx.draw_networkx_edges(
        G,
        pos,
        edge_color=edge_colors,
        width=edge_widths
    )

    plt.title(title)

    plt.axis("off")

    plt.tight_layout()

    plt.show()


# ============================================================
# EJEMPLO DE USO
# ============================================================

"""
history = {
    "H_i": [...],
    "I_i": [...],
    ...
    "we_j": [...]
}

results = analyze_dyadic_coupling(
    history,
    theta=0.3
)

print()

print("========== NIVEL 2 ==========")

print("Q:", results["Q"])

print(
    "Inter-density:",
    results["inter_density"]
)

print(
    "Intra-density:",
    results["intra_density"]
)

print(
    "Asymmetry Index:",
    results["asymmetry_index"]
)

print()

print("Comunidades:")

for c in results["communities"]:
    print(c)

plot_dyadic_graph(
    results["graph"]
)
"""