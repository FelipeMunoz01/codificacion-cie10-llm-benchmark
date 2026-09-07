"""Figuras del informe de Fase 1. Lee resultados/ y escribe figuras/.

    python src/figuras.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = Path(__file__).resolve().parent.parent
RES = RAIZ / "resultados"
FIG = RAIZ / "figuras"
FIG.mkdir(exist_ok=True)

AZUL, GRIS, VERDE, ROJO = "#2563eb", "#94a3b8", "#059669", "#dc2626"
plt.rcParams.update({"font.size": 10, "figure.dpi": 130, "savefig.bbox": "tight"})


def _filas_jsonl():
    """Última fila por config, priorizando la n más alta."""
    filas = [json.loads(l) for l in (RES / "eval_codificador.jsonl").read_text().splitlines() if l.strip()]
    por = {}
    for f in filas:
        c = f["config"]
        if c not in por or f["n"] >= por[c]["n"]:
            por[c] = f
    return por


def fig_ablations(por: dict) -> None:
    orden = [
        ("gpt-4o-mini_concand_pmin", "mini\nprompt mínimo"),
        ("gpt-4o-mini_sincand", "mini\nsin candidatos"),
        ("gpt-4o-mini_concand", "mini\ncon candidatos"),
        ("gpt-4o-mini_concand_fewshot", "mini\n+ few-shot"),
        ("gpt-4o_concand", "gpt-4o\ncon candidatos"),
    ]
    orden = [(k, v) for k, v in orden if k in por]
    etqs = [v for _, v in orden]
    ex = [por[k]["MAP"] for k, _ in orden]
    c3 = [por[k].get("MAP_cat3", 0) for k, _ in orden]
    x = range(len(orden))
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar([i - 0.2 for i in x], c3, 0.4, label="MAP categoría (3 car.)", color=GRIS)
    ax.bar([i + 0.2 for i in x], ex, 0.4, label="MAP exacto", color=AZUL)
    ax.axhline(0.593, ls="--", color=ROJO, lw=1)
    ax.text(len(orden) - 0.5, 0.60, "mejor sistema CodiEsp-D 2020 (supervisado): 0,593",
            ha="right", va="bottom", color=ROJO, fontsize=8)
    ax.set_xticks(list(x)); ax.set_xticklabels(etqs)
    ax.set_ylabel("MAP"); ax.set_ylim(0, 0.66)
    ax.set_title("Codificación CIE-10-ES: MAP por configuración (dev)")
    ax.legend(loc="upper left"); ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(FIG / "fig_map_por_config.png")
    plt.close(fig)


def fig_recall_retrieval() -> None:
    # de resultados/eval_retrieval_dev.md (committeado)
    ks = [20, 50, 100, 150, 200, 300, 500]
    series = {
        "documento completo (denso)": [.043, .060, .082, .100, .108, .124, .161],
        "por frases, híbrido": [.093, .156, .224, .268, .307, .354, .405],
    }
    techo = 0.516
    fig, ax = plt.subplots(figsize=(7, 4))
    for etq, ys in series.items():
        ax.plot(ks, ys, marker="o", label=etq)
    ax.axhline(techo, ls="--", color=GRIS)
    ax.text(500, techo + 0.01, f"techo de la unión: {techo:.2f}", ha="right", fontsize=8, color=GRIS)
    ax.set_xlabel("k (nº de códigos candidatos)"); ax.set_ylabel("recall@k")
    ax.set_title("Recuperación pura: fracción del gold entre los k candidatos (dev)")
    ax.set_ylim(0, 0.6); ax.legend(); ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(FIG / "fig_recall_retrieval.png")
    plt.close(fig)


def fig_costo_map(por: dict) -> None:
    pts = [
        ("gpt-4o-mini", por.get("gpt-4o-mini_concand", {})),
        ("gpt-4o", por.get("gpt-4o_concand", {})),
    ]
    pts = [(n, d) for n, d in pts if d]
    fig, ax = plt.subplots(figsize=(6, 4))
    for n, d in pts:
        ax.scatter(d["costo_1000casos_usd"], d["MAP"], s=80, color=AZUL)
        ax.annotate(f"  {n}\n  MAP {d['MAP']}", (d["costo_1000casos_usd"], d["MAP"]), fontsize=9)
    ax.set_xlabel("costo por 1000 casos (USD)"); ax.set_ylabel("MAP exacto")
    ax.set_title("Costo vs. exactitud"); ax.set_xscale("log")
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(FIG / "fig_costo_map.png")
    plt.close(fig)


def fig_errores() -> None:
    md = RES / "analisis_errores_gpt-4o-mini_concand.md"
    if not md.exists():
        print("(sin análisis de errores todavía, omito fig_errores)")
        return
    import re
    texto = md.read_text()
    bloque = texto.split("## Destino de cada código GOLD")[1].split("##")[0]
    pares = re.findall(r"\| ([^|]+?) \| (\d+) \| [\d.]+% \|", bloque)
    etqs = [p[0].strip() for p in pares]
    vals = [int(p[1]) for p in pares]
    colores = [VERDE, "#a7f3d0", "#fcd34d", GRIS, ROJO][: len(vals)]
    fig, ax = plt.subplots(figsize=(8, 3.2))
    izq = 0
    tot = sum(vals)
    for e, v, c in zip(etqs, vals, colores):
        ax.barh(0, v, left=izq, color=c, label=f"{e} ({100*v/tot:.0f}%)")
        izq += v
    ax.set_yticks([]); ax.set_xlim(0, tot)
    ax.set_title("Destino de cada código gold (gpt-4o-mini, dev)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=8, frameon=False)
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.savefig(FIG / "fig_destino_gold.png")
    plt.close(fig)


def main() -> None:
    por = _filas_jsonl()
    fig_ablations(por)
    fig_recall_retrieval()
    fig_costo_map(por)
    fig_errores()
    print("figuras en", FIG.relative_to(RAIZ))


if __name__ == "__main__":
    main()
