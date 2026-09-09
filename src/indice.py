"""Bloque B: base de conocimiento e índice de recuperación.

Para el subtrack elegido (D diagnósticos, P procedimientos) construye, a partir de la
lista oficial de códigos CIE-10-ES:
  - un diccionario normalizado (código + descripción)  -> data/index/dicc_<S>.csv
  - embeddings de cada código (text-embedding-3-small, dimensions=512)
                                                        -> data/index/emb_<S>.npy
  - un manifiesto con el modelo, dimensión, fecha, hash -> data/index/manifiesto_<S>.json

Nada de esto se versiona (ver .gitignore). Se regenera con `python src/indice.py`.

Uso:
    python src/indice.py --subtrack D
    python src/indice.py --subtrack P --forzar
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


def _rutas(subtrack: str) -> tuple[Path, Path, Path]:
    s = subtrack.upper()
    return (DIR_INDICE / f"dicc_{s}.csv",
            DIR_INDICE / f"emb_{s}.npy",
            DIR_INDICE / f"manifiesto_{s}.json")


def _texto_codigo(cod: str, desc: str) -> str:
    return f"{cod.upper()}: {desc}"


def construir_diccionario(subtrack: str = "D") -> pd.DataFrame:
    """codigo, desc_es, texto (lo que se indexa)."""
    dicc = cargar_diccionario(subtrack)[["codigo", "desc_es"]].copy()
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


def cargar_indice(subtrack: str = "D") -> tuple[pd.DataFrame, np.ndarray]:
    """Devuelve (diccionario, embeddings float32 normalizados) del subtrack."""
    ruta_csv, ruta_emb, _ = _rutas(subtrack)
    dicc = pd.read_csv(ruta_csv, dtype=str)
    emb = np.load(ruta_emb).astype(np.float32)
    return dicc, emb


def construir(subtrack: str = "D", forzar: bool = False) -> None:
    DIR_INDICE.mkdir(parents=True, exist_ok=True)
    ruta_csv, ruta_emb, ruta_manif = _rutas(subtrack)

    dicc = construir_diccionario(subtrack)
    dicc.to_csv(ruta_csv, index=False)
    print(f"diccionario {subtrack}: {len(dicc):,} códigos -> {ruta_csv.relative_to(RAIZ)}")

    textos = dicc["texto"].tolist()
    hash_actual = _hash_textos(textos)

    if ruta_emb.exists() and not forzar:
        manif = json.loads(ruta_manif.read_text()) if ruta_manif.exists() else {}
        if manif.get("hash_textos") == hash_actual:
            print(f"embeddings ya al día: {np.load(ruta_emb).shape}")
            return
        print("el diccionario cambió, se regeneran los embeddings")

    print(f"generando embeddings ({MODELO_EMB}, dim={DIMS})...")
    emb = generar_embeddings(textos)
    np.save(ruta_emb, emb.astype(np.float16))
    ruta_manif.write_text(
        json.dumps(
            {
                "subtrack": subtrack.upper(),
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
    print(f"embeddings: {emb.shape} -> {ruta_emb.relative_to(RAIZ)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--subtrack", default="D", choices=["D", "P"])
    ap.add_argument("--forzar", action="store_true", help="reconstruir aunque exista")
    a = ap.parse_args()
    construir(subtrack=a.subtrack, forzar=a.forzar)
