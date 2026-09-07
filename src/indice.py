"""Bloque B: base de conocimiento e índice de recuperación (subtrack D).

Construye, a partir de la lista oficial de códigos CIE-10-ES:
  - un diccionario normalizado (código + descripción)      -> data/index/dicc_D.csv
  - embeddings de cada código (OpenAI text-embedding-3-small, dimensions=512)
                                                            -> data/index/emb_D.npy
  - un manifiesto con el modelo, dimensión, fecha y hash    -> data/index/manifiesto_D.json

Nada de esto se versiona (ver .gitignore). Se regenera con `python src/indice.py`
(coste puntual ~USD 0,06). El manifiesto documenta el modelo exacto usado.

Uso:
    python src/indice.py            # construye lo que falte
    python src/indice.py --forzar   # reconstruye aunque exista
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv

from datos import cargar_diccionario

RAIZ = Path(__file__).resolve().parent.parent
DIR_INDICE = RAIZ / "data" / "index"

MODELO_EMB = "text-embedding-3-small"
DIMS = 512
LOTE = 1000  # inputs por petición a la API

RUTA_CSV = DIR_INDICE / "dicc_D.csv"
RUTA_EMB = DIR_INDICE / "emb_D.npy"
RUTA_MANIF = DIR_INDICE / "manifiesto_D.json"


def _texto_codigo(cod: str, desc: str) -> str:
    """Documento que se indexa por cada código."""
    return f"{cod.upper()}: {desc}"


def construir_diccionario() -> pd.DataFrame:
    """codigo, desc_es, texto (lo que se indexa)."""
    dicc = cargar_diccionario("D")[["codigo", "desc_es"]].copy()
    dicc["texto"] = [_texto_codigo(c, d) for c, d in zip(dicc["codigo"], dicc["desc_es"])]
    return dicc.reset_index(drop=True)


def _hash_textos(textos: list[str]) -> str:
    h = hashlib.sha256()
    for t in textos:
        h.update(t.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()[:16]


def _cliente_openai():
    from openai import OpenAI

    load_dotenv(RAIZ / ".env")
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def embed_textos(textos: list[str], cliente=None, log: bool = True) -> np.ndarray:
    """Embeddings L2-normalizados (float32) de una lista de textos."""
    cliente = cliente or _cliente_openai()
    vecs: list[list[float]] = []
    t0 = time.time()
    for i in range(0, len(textos), LOTE):
        resp = cliente.embeddings.create(
            model=MODELO_EMB, input=textos[i : i + LOTE], dimensions=DIMS
        )
        vecs.extend(d.embedding for d in resp.data)
        if log:
            print(f"  {len(vecs):>7} / {len(textos)}  ({time.time() - t0:.0f} s)", end="\r")
    if log:
        print()
    arr = np.asarray(vecs, dtype=np.float32)
    arr /= np.linalg.norm(arr, axis=1, keepdims=True) + 1e-12
    return arr


def generar_embeddings(textos: list[str]) -> np.ndarray:
    return embed_textos(textos)


def cargar_indice() -> tuple[pd.DataFrame, np.ndarray]:
    """Devuelve (diccionario, embeddings float32 normalizados)."""
    dicc = pd.read_csv(RUTA_CSV, dtype=str)
    emb = np.load(RUTA_EMB).astype(np.float32)
    return dicc, emb


def construir(forzar: bool = False) -> None:
    DIR_INDICE.mkdir(parents=True, exist_ok=True)

    dicc = construir_diccionario()
    dicc.to_csv(RUTA_CSV, index=False)
    print(f"diccionario: {len(dicc):,} códigos -> {RUTA_CSV.relative_to(RAIZ)}")

    textos = dicc["texto"].tolist()
    hash_actual = _hash_textos(textos)

    if RUTA_EMB.exists() and not forzar:
        manif = json.loads(RUTA_MANIF.read_text()) if RUTA_MANIF.exists() else {}
        if manif.get("hash_textos") == hash_actual:
            print(f"embeddings ya al día: {np.load(RUTA_EMB).shape}")
            return
        print("el diccionario cambió, se regeneran los embeddings")

    print(f"generando embeddings ({MODELO_EMB}, dim={DIMS})...")
    emb = generar_embeddings(textos)
    np.save(RUTA_EMB, emb.astype(np.float16))  # fp16 en disco
    RUTA_MANIF.write_text(
        json.dumps(
            {
                "modelo": MODELO_EMB,
                "dimensiones": DIMS,
                "n_codigos": len(dicc),
                "hash_textos": hash_actual,
                "fecha": date.today().isoformat(),
                "forma_embeddings": list(emb.shape),
                "nota": "normalizada L2; en disco float16; regenerar con src/indice.py",
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    print(f"embeddings: {emb.shape} -> {RUTA_EMB.relative_to(RAIZ)}")
    print(f"manifiesto -> {RUTA_MANIF.relative_to(RAIZ)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--forzar", action="store_true", help="reconstruir aunque exista")
    construir(forzar=ap.parse_args().forzar)
