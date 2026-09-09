"""Bloque C / D: evaluar el codificador LLM sobre CodiEsp-D.

Métricas:
  - MAP  : mean average precision sobre la lista ordenada de códigos (métrica oficial
           de CodiEsp-D).
  - P/R/F1 micro : a nivel de código, con el corte natural (todo lo que predice).
  - códigos/caso, tasa de alucinación, coste.

    python src/eval_codificador.py --n 50                 # gpt-4o-mini, con candidatos
    python src/eval_codificador.py --n 50 --sin-candidatos
    python src/eval_codificador.py --n 50 --few-shot
    python src/eval_codificador.py --n 50 --modelo gpt-4o

Cachea los candidatos recuperados por caso en data/index/cand_<split>.json.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from codificador import Codificador
from datos import cargar_casos, cargar_gold
from recuperar import Recuperador, frases_de, _topk, rrf

RAIZ = Path(__file__).resolve().parent.parent
DIR_INDICE = RAIZ / "data" / "index"
PRECIO = {  # USD por 1M tokens (prompt, completion)
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
}


def candidatos_split(split: str, subtrack: str = "D", k: int = 150) -> dict[str, list[str]]:
    ruta = DIR_INDICE / f"cand_{split}_{subtrack}.json"
    if ruta.exists():
        return json.loads(ruta.read_text())
    casos = cargar_casos(split)
    rec = Recuperador(subtrack)
    emb = np.load(DIR_INDICE / f"emb_frases_{split}.npy").astype(np.float32)
    frs = [frases_de(t) for t in casos["texto"]]
    ef, i = [], 0
    for f in frs:
        ef.append(emb[i : i + len(f)])
        i += len(f)
    out = {
        cid: rec.candidatos(fs, e, k=k, k_frase=30, usar_bm25=True)
        for cid, fs, e in zip(casos["id"], frs, ef)
    }
    ruta.write_text(json.dumps(out))
    return out


def average_precision(ranked: list[str], gold: set[str]) -> float:
    if not gold:
        return 0.0
    aciertos = 0
    suma = 0.0
    for i, c in enumerate(ranked, 1):
        if c in gold:
            aciertos += 1
            suma += aciertos / i
    return suma / len(gold)


def cat3(c: str) -> str:
    return c.replace(".", "")[:3]


def metricas(pred: list[str], gold: set[str], nivel: str = "exacto"):
    if nivel == "cat3":
        p = list(dict.fromkeys(cat3(c) for c in pred))
        g = {cat3(c) for c in gold}
    else:
        p, g = pred, gold
    tp = len(set(p) & set(g))
    P = tp / len(p) if p else 0.0
    R = tp / len(g) if g else 0.0
    F = 2 * P * R / (P + R) if P + R else 0.0
    return P, R, F, average_precision(list(p), set(g))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=["train", "dev", "test"])
    ap.add_argument("--subtrack", default="D", choices=["D", "P"])
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--modelo", default="gpt-4o-mini")
    ap.add_argument("--sin-candidatos", action="store_true")
    ap.add_argument("--few-shot", action="store_true")
    ap.add_argument("--prompt-min", action="store_true")
    a = ap.parse_args()

    casos = cargar_casos(a.split).head(a.n)
    gold = cargar_gold(a.split, a.subtrack)
    golds = {cid: set(gold.loc[gold["id"] == cid, "codigo"]) for cid in casos["id"]}
    cand = {} if a.sin_candidatos else candidatos_split(a.split, a.subtrack)

    etq = (f"{a.subtrack}_{a.modelo}"
           f"{'_sincand' if a.sin_candidatos else '_concand'}"
           f"{"_fewshot" if a.few_shot else ""}{"_pmin" if a.prompt_min else ""}")
    cache_pred = DIR_INDICE / f"pred_{a.split}_{etq}.json"
    predicho: dict = json.loads(cache_pred.read_text()) if cache_pred.exists() else {}

    cod = None
    ex, c3, npred, naluc = [], [], [], []
    tok_p = tok_c = 0
    t0 = time.time()
    n_api = 0
    for k, cid in enumerate(casos["id"], 1):
        texto = casos.loc[casos["id"] == cid, "texto"].iloc[0]
        g = golds[cid]
        if cid in predicho:
            pred = predicho[cid]["codigos"]
            naluc.append(predicho[cid].get("aluc", 0))
        else:
            if cod is None:
                cod = Codificador(modelo=a.modelo, few_shot=a.few_shot,
                                  prompt_min=a.prompt_min, subtrack=a.subtrack)
            r = cod.codificar(texto, candidatos=cand.get(cid))
            pred = r.codigos
            predicho[cid] = {"codigos": pred, "aluc": len(r.alucinados)}
            naluc.append(len(r.alucinados))
            tok_p += r.uso["prompt"]; tok_c += r.uso["completion"]
            n_api += 1
            if n_api % 10 == 0:
                cache_pred.write_text(json.dumps(predicho))
        ex.append(metricas(pred, g, "exacto"))
        c3.append(metricas(pred, g, "cat3"))
        npred.append(len(pred))
        if k % 10 == 0:
            print(f"  {k}/{len(casos)}  MAP={np.mean([x[3] for x in ex]):.3f} "
                  f"F1={np.mean([x[2] for x in ex]):.3f} ({time.time()-t0:.0f}s)")
    cache_pred.write_text(json.dumps(predicho))

    def prom(rows, i):
        return round(float(np.mean([r[i] for r in rows])), 3)

    pp, pc = PRECIO.get(a.modelo, (0, 0))
    costo = tok_p / 1e6 * pp + tok_c / 1e6 * pc
    resumen = {
        "config": etq,
        "n": len(casos),
        "MAP": prom(ex, 3),
        "F1_micro": prom(ex, 2),
        "P": prom(ex, 0),
        "R": prom(ex, 1),
        "MAP_cat3": prom(c3, 3),
        "F1_cat3": prom(c3, 2),
        "R_cat3": prom(c3, 1),
        "cods_pred/caso": round(float(np.mean(npred)), 1),
        "cods_gold/caso": round(
            gold.groupby("id").size().reindex(casos["id"]).fillna(0).mean(), 1),
        "alucinac/caso": round(float(np.mean(naluc)), 2),
        "costo_usd_corrida": round(costo, 3),
        "costo_1000casos_usd": round(costo / n_api * 1000, 2) if n_api else None,
        "seg/caso": round((time.time() - t0) / len(casos), 1),
    }
    print("\n" + json.dumps(resumen, indent=2, ensure_ascii=False))

    hist = RAIZ / "resultados" / "eval_codificador.jsonl"
    with hist.open("a") as fh:
        fh.write(json.dumps(resumen, ensure_ascii=False) + "\n")
    print(f"\nañadido a {hist.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
