"""Bloque D, paso 1.17: análisis de errores del codificador.

Toma las predicciones cacheadas de una config (data/index/pred_<split>_<config>.json)
y clasifica cada código gold y cada código predicho para entender de qué tipo son los
fallos.

    python src/analisis_errores.py --config gpt-4o-mini_concand --split dev --n 100
"""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

import numpy as np

from datos import cargar_casos, cargar_gold, cargar_diccionario

RAIZ = Path(__file__).resolve().parent.parent
DIR_INDICE = RAIZ / "data" / "index"

VAGOS = ("no especificad", "neom", "nom", "sin otra especif", "no clasificad",
         "otros trastornos", "otras enfermedades", "otras especificad", "otro ")


def cat3(c: str) -> str:
    return c.replace(".", "")[:3]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--split", default="dev")
    ap.add_argument("--n", type=int, default=100)
    a = ap.parse_args()

    pred = json.loads((DIR_INDICE / f"pred_{a.split}_{a.config}.json").read_text())
    cand = json.loads((DIR_INDICE / f"cand_{a.split}.json").read_text())
    casos = cargar_casos(a.split).head(a.n)
    gold = cargar_gold(a.split, "D")
    dicc = cargar_diccionario("D")
    desc = dict(zip(dicc["codigo"], dicc["desc_es"]))

    def es_vago(c):
        return any(k in desc.get(c, "").lower() for k in VAGOS)

    g_exacto = g_cat3 = g_fallo_en_cand = g_fallo_vago = g_fallo_otro = 0
    p_correcto = p_cat3 = p_sobra = 0
    n_gold = n_pred = 0
    ej_sobra, ej_falla = [], []

    for cid in casos["id"]:
        if cid not in pred:
            continue
        P = pred[cid]["codigos"]
        G = set(gold.loc[gold["id"] == cid, "codigo"])
        C = set(cand.get(cid, []))
        Pset, Pc3 = set(P), {cat3(c) for c in P}
        Gc3 = {cat3(c) for c in G}
        n_gold += len(G); n_pred += len(P)

        for c in G:
            if c in Pset:
                g_exacto += 1
            elif cat3(c) in Pc3:
                g_cat3 += 1
            elif c in C:
                g_fallo_en_cand += 1
                if len(ej_falla) < 12:
                    ej_falla.append((cid, c, desc.get(c, "")[:55], "estaba en candidatos"))
            elif es_vago(c):
                g_fallo_vago += 1
            else:
                g_fallo_otro += 1
                if len(ej_falla) < 12:
                    ej_falla.append((cid, c, desc.get(c, "")[:55], "no recuperado"))

        for c in P:
            if c in G:
                p_correcto += 1
            elif cat3(c) in Gc3:
                p_cat3 += 1
            else:
                p_sobra += 1
                if len(ej_sobra) < 12:
                    ej_sobra.append((cid, c, desc.get(c, "")[:55]))

    buf = io.StringIO()
    w = buf.write
    w(f"# Análisis de errores - {a.config} ({a.split}, {len(casos)} casos)\n\n")
    w(f"{n_gold} códigos gold, {n_pred} predichos.\n\n")
    w("## Destino de cada código GOLD\n\n")
    w("| categoría | n | % |\n|---|---|---|\n")
    for etq, v in [
        ("acierto exacto", g_exacto),
        ("categoría correcta, especificidad equivocada", g_cat3),
        ("fallo: estaba en los candidatos, el LLM no lo eligió", g_fallo_en_cand),
        ("fallo: código vago sin anclaje textual", g_fallo_vago),
        ("fallo: otro (no recuperado, no vago)", g_fallo_otro),
    ]:
        w(f"| {etq} | {v} | {100*v/n_gold:.1f}% |\n")
    w("\n## Destino de cada código PREDICHO\n\n")
    w("| categoría | n | % |\n|---|---|---|\n")
    for etq, v in [
        ("correcto (exacto)", p_correcto),
        ("categoría correcta, especificidad equivocada", p_cat3),
        ("sobrecodificación (ni exacto ni categoría)", p_sobra),
    ]:
        w(f"| {etq} | {v} | {100*v/n_pred:.1f}% |\n")
    w("\n## Ejemplos de gold no acertado\n\n")
    for cid, c, d, motivo in ej_falla:
        w(f"- `{c}` {d} ({motivo}) — {cid}\n")
    w("\n## Ejemplos de sobrecodificación\n\n")
    for cid, c, d in ej_sobra:
        w(f"- `{c}` {d} — {cid}\n")

    salida = RAIZ / "resultados" / f"analisis_errores_{a.config}.md"
    salida.write_text(buf.getvalue(), encoding="utf-8")
    print(buf.getvalue())
    print(f"guardado en {salida.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
