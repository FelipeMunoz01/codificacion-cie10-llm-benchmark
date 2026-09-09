"""Bloque B, paso 1.9: evaluar SOLO la recuperación.

Compara estrategias de consulta (documento completo vs por frases) y mide
recall@k = |recuperados ∩ gold| / |gold|, promediado sobre casos. Ese recall es el
techo de F1 que el codificador LLM podrá alcanzar después.

    python src/eval_retrieval.py --split dev

Cachea los embeddings de casos y de frases en data/index/ para que las corridas
repetidas de los ablations sean rápidas y sin coste.
"""

from __future__ import annotations

import argparse
import io
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from datos import cargar_casos, cargar_gold
from indice import DIMS, MODELO_EMB, embed_textos
from recuperar import Recuperador, frases_de, rrf, _topk

RAIZ = Path(__file__).resolve().parent.parent
DIR_INDICE = RAIZ / "data" / "index"
KS = [20, 50, 100, 150, 200, 300, 500]
KMAX = max(KS)


def _cache_emb(nombre: str, textos: list[str], cliente) -> np.ndarray:
    ruta = DIR_INDICE / f"{nombre}.npy"
    if ruta.exists():
        m = np.load(ruta)
        if m.shape == (len(textos), DIMS):
            return m
    print(f"embebiendo {len(textos)} textos ({nombre})...")
    m = embed_textos(textos, cliente=cliente)
    np.save(ruta, m.astype(np.float16))
    return m.astype(np.float32)


def tabla_md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(
            f"{v:.3f}" if isinstance(v, float) else str(v) for v in r
        ) + " |")
    return "\n".join(out)


def recall_tabla(nombre: str, cands: list[list[str]], golds: list[set[str]]) -> dict:
    fila = {"estrategia": nombre}
    for k in KS:
        vals = [len(set(c[:k]) & g) / len(g) for c, g in zip(cands, golds) if g]
        fila[f"r@{k}"] = float(np.mean(vals))
    return fila


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=["train", "dev", "test"])
    ap.add_argument("--subtrack", default="D", choices=["D", "P"])
    args = ap.parse_args(); split = args.split; subtrack = args.subtrack

    casos = cargar_casos(split)
    gold = cargar_gold(split, subtrack)
    golds = [set(gold.loc[gold["id"] == cid, "codigo"]) for cid in casos["id"]]

    rec = Recuperador(subtrack)

    # embeddings de documento completo (baseline) y de frases (cacheados)
    emb_doc = _cache_emb(f"emb_casos_{split}", casos["texto"].tolist(), rec._cliente)

    frases_por_caso = [frases_de(t) for t in casos["texto"]]
    plano = [f for fs in frases_por_caso for f in fs]
    emb_plano = _cache_emb(f"emb_frases_{split}", plano, rec._cliente)
    # re-agrupar por caso
    emb_frases, i = [], 0
    for fs in frases_por_caso:
        emb_frases.append(emb_plano[i : i + len(fs)])
        i += len(fs)

    n_fr = np.mean([len(fs) for fs in frases_por_caso])
    print(f"{len(casos)} casos, {n_fr:.1f} frases/caso, "
          f"{gold.groupby('id').size().mean():.1f} códigos/caso")

    filas = []
    t0 = time.time()

    c_doc = [rec.codigos[_topk(rec.emb @ v, KMAX)].tolist() for v in emb_doc]
    filas.append(recall_tabla("doc-denso", c_doc, golds))

    for kf in (30, 50):
        cands = [
            rec.candidatos(fs, ef, k=KMAX, k_frase=kf, usar_bm25=False)
            for fs, ef in zip(frases_por_caso, emb_frases)
        ]
        filas.append(recall_tabla(f"frase-denso (kf={kf})", cands, golds))
        cands = [
            rec.candidatos(fs, ef, k=KMAX, k_frase=kf, usar_bm25=True)
            for fs, ef in zip(frases_por_caso, emb_frases)
        ]
        filas.append(recall_tabla(f"frase-hibrido (kf={kf})", cands, golds))

    # techo: unión sin fusionar ni recortar, denso+bm25 top-50 por frase
    techo = []
    for fs, ef in zip(frases_por_caso, emb_frases):
        pool = set()
        for v in ef:
            pool.update(rec.codigos[_topk(rec.emb @ v, 50)].tolist())
        for f in fs:
            pool.update(rec.codigos[_topk(rec.bm25_scores(f), 50)].tolist())
        techo.append(list(pool))
    fila_techo = {"estrategia": "TECHO union (kf=50, sin cap)"}
    vals = [len(set(c) & g) / len(g) for c, g in zip(techo, golds) if g]
    for k in KS:
        fila_techo[f"r@{k}"] = float(np.mean(vals))  # constante: es la unión completa
    filas.append(fila_techo)

    print(f"recuperación lista en {time.time() - t0:.0f} s")
    tabla = pd.DataFrame(filas)

    buf = io.StringIO()
    buf.write(f"# Recuperación pura - recall@k (split {split}, subtrack {subtrack})\n\n")
    buf.write(f"Embeddings: {MODELO_EMB} dim {DIMS}. {len(casos)} casos, "
              f"{n_fr:.1f} frases/caso, {gold.groupby('id').size().mean():.1f} códigos/caso.\n\n")
    buf.write("recall@k = fracción de códigos gold del caso presentes entre los k "
              "candidatos, promediada sobre casos.\n\n")
    buf.write(tabla_md(tabla) + "\n")
    (RAIZ / "resultados" / f"eval_retrieval_{split}_{subtrack}.md").write_text(buf.getvalue(), encoding="utf-8")
    print("\n" + buf.getvalue())


if __name__ == "__main__":
    main()
