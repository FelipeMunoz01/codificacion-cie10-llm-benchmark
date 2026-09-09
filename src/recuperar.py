"""Bloque B: buscadores de códigos candidatos (denso, léxico y híbrido).

Dado el texto de un caso clínico, cada buscador devuelve una lista ordenada de
códigos CIE-10-ES candidatos.

    from recuperar import Recuperador
    r = Recuperador()
    r.denso(texto, k=20)
    r.bm25(texto, k=20)
    r.hibrido(texto, k=20)

BM25 está implementado sobre una matriz término-documento dispersa (scipy). El
`rank_bm25` de PyPI hace un bucle Python sobre los ~98 mil documentos por término de
la consulta y es demasiado lento para las corridas repetidas de los ablations.
"""

from __future__ import annotations

import os
import re
from functools import cached_property
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from scipy.sparse import csr_matrix

from indice import DIMS, MODELO_EMB, cargar_indice

RAIZ = Path(__file__).resolve().parent.parent
_TOKEN = re.compile(r"[0-9a-záéíóúñü]+")
_CORTE_FRASE = re.compile(r"(?<=[.!?])\s+|\n+|\s+-\s+")
_ES_MEDIDA = re.compile(r"\d+([.,]\d+)?\s*(mg|g|ml|dl|mm|cm|mmol|meq|mmhg|mcg|ui|u/l|/mm|kg|mg/dl|"
                        r"mm/h|lpm|rpm|ºc|°c|%)", re.IGNORECASE)

K1 = 1.5
B = 0.75

# Abreviaturas clínicas frecuentes en español -> término expandido. Se anexan a la
# frase antes de consultar para que el índice (que solo tiene descripciones formales)
# pueda emparejarlas.
ABREVIATURAS = {
    "hta": "hipertensión arterial", "dm": "diabetes mellitus",
    "dm2": "diabetes mellitus tipo 2", "dm1": "diabetes mellitus tipo 1",
    "dmid": "diabetes mellitus insulinodependiente", "irc": "insuficiencia renal crónica",
    "erc": "enfermedad renal crónica", "ira": "insuficiencia renal aguda",
    "itu": "infección del tracto urinario", "epoc": "enfermedad pulmonar obstructiva crónica",
    "iam": "infarto agudo de miocardio", "icc": "insuficiencia cardíaca congestiva",
    "ic": "insuficiencia cardíaca", "fa": "fibrilación auricular",
    "acv": "accidente cerebrovascular", "avc": "accidente cerebrovascular",
    "tvp": "trombosis venosa profunda", "tep": "tromboembolismo pulmonar",
    "hda": "hemorragia digestiva alta", "hdb": "hemorragia digestiva baja",
    "erge": "enfermedad por reflujo gastroesofágico", "hbp": "hiperplasia benigna de próstata",
    "vih": "virus de la inmunodeficiencia humana", "ivu": "infección de vías urinarias",
    "dlp": "dislipidemia", "avm": "asistencia ventilatoria mecánica",
    "eii": "enfermedad inflamatoria intestinal", "les": "lupus eritematoso sistémico",
    "ar": "artritis reumatoide", "acxfa": "fibrilación auricular",
}


def tokenizar(texto: str) -> list[str]:
    return [t for t in _TOKEN.findall(texto.lower()) if len(t) > 2]


def _expandir_abreviaturas(frase: str) -> str:
    extra = {ABREVIATURAS[t] for t in set(tokenizar(frase)) if t in ABREVIATURAS}
    return frase + (" " + " ; ".join(sorted(extra)) if extra else "")


def frases_de(texto: str, min_car: int = 20, exp_abrev: bool = True) -> list[str]:
    """Parte un caso clínico en frases para consultar por separado.

    - corta en fin de oración y saltos de línea (no en ';' ni ':', que dentro de las
      epicrisis separan ítems de laboratorio y no ideas)
    - descarta fragmentos que son casi solo valores de laboratorio
    - fusiona fragmentos muy cortos con el anterior
    - opcionalmente anexa la expansión de abreviaturas clínicas
    """
    crudas = [f.strip() for f in _CORTE_FRASE.split(texto) if f.strip()]
    fusion: list[str] = []
    for f in crudas:
        if fusion and len(f) < 30:
            fusion[-1] = fusion[-1] + " " + f
        else:
            fusion.append(f)
    out = []
    for f in fusion:
        if len(f) < min_car:
            continue
        letras = sum(c.isalpha() for c in f)
        if letras < 0.5 * len(f) or len(_ES_MEDIDA.findall(f)) >= 3:
            continue  # línea de laboratorio / mediciones
        out.append(_expandir_abreviaturas(f) if exp_abrev else f)
    return out


def rrf(rankings: list[np.ndarray], k: int, k_rrf: int = 60) -> list[int]:
    """Fusión por rango recíproco de varias listas de índices ya ordenadas."""
    pts: dict[int, float] = {}
    for r in rankings:
        for rango, doc in enumerate(r):
            pts[doc] = pts.get(doc, 0.0) + 1.0 / (k_rrf + rango)
    return sorted(pts, key=pts.get, reverse=True)[:k]


class _BM25Disperso:
    """BM25 Okapi sobre una matriz término-documento CSC."""

    def __init__(self, textos: list[str]) -> None:
        vocab: dict[str, int] = {}
        indptr = [0]
        indices: list[int] = []
        data: list[float] = []
        for txt in textos:
            cuentas: dict[int, int] = {}
            for tok in tokenizar(txt):
                j = vocab.setdefault(tok, len(vocab))
                cuentas[j] = cuentas.get(j, 0) + 1
            indices.extend(cuentas.keys())
            data.extend(cuentas.values())
            indptr.append(len(indices))

        n_docs, n_term = len(textos), len(vocab)
        X = csr_matrix(
            (np.asarray(data, np.float32), np.asarray(indices), np.asarray(indptr)),
            shape=(n_docs, n_term),
        )
        self.vocab = vocab
        self.X = X.tocsc()  # CSC: corte por columnas (términos de la consulta) rápido
        doc_len = np.asarray(X.sum(axis=1)).ravel()
        avgdl = doc_len.mean()
        df = np.asarray((X > 0).sum(axis=0)).ravel()
        self.idf = np.log((n_docs - df + 0.5) / (df + 0.5) + 1.0).astype(np.float32)
        self.b_doc = (K1 * (1 - B + B * doc_len / avgdl)).astype(np.float32)
        self.n_docs = n_docs

    def scores(self, texto: str) -> np.ndarray:
        cols = [self.vocab[t] for t in set(tokenizar(texto)) if t in self.vocab]
        out = np.zeros(self.n_docs, dtype=np.float32)
        if not cols:
            return out
        sub = self.X[:, cols].tocoo()
        idf_c = self.idf[np.asarray(cols)][sub.col]
        v = sub.data
        contrib = idf_c * (v * (K1 + 1)) / (v + self.b_doc[sub.row])
        np.add.at(out, sub.row, contrib)
        return out


def _topk(puntajes: np.ndarray, k: int) -> np.ndarray:
    k = min(k, len(puntajes))
    idx = np.argpartition(-puntajes, k - 1)[:k]
    return idx[np.argsort(-puntajes[idx])]


class Recuperador:
    def __init__(self, subtrack: str = "D") -> None:
        self.subtrack = subtrack.upper()
        self.dicc, self.emb = cargar_indice(subtrack)  # emb (N, DIMS) float32 normalizada
        self.codigos = self.dicc["codigo"].to_numpy()
        load_dotenv(RAIZ / ".env")
        from openai import OpenAI

        self._cliente = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    # --- denso ---
    def embed_consulta(self, texto: str) -> np.ndarray:
        resp = self._cliente.embeddings.create(
            model=MODELO_EMB, input=[texto], dimensions=DIMS
        )
        v = np.asarray(resp.data[0].embedding, dtype=np.float32)
        return v / (np.linalg.norm(v) + 1e-12)

    def denso_desde_vector(self, v: np.ndarray, k: int = 20) -> list[str]:
        return self.codigos[_topk(self.emb @ v, k)].tolist()

    def denso(self, texto: str, k: int = 20) -> list[str]:
        return self.denso_desde_vector(self.embed_consulta(texto), k)

    # --- léxico ---
    @cached_property
    def _bm25(self) -> _BM25Disperso:
        return _BM25Disperso(self.dicc["texto"].tolist())

    def bm25_scores(self, texto: str) -> np.ndarray:
        return self._bm25.scores(texto)

    def bm25(self, texto: str, k: int = 20) -> list[str]:
        return self.codigos[_topk(self.bm25_scores(texto), k)].tolist()

    # --- híbrido: fusión por rango recíproco (RRF) ---
    def rrf_desde(self, sims: np.ndarray, sc_bm25: np.ndarray, k: int, tope: int = 200,
                  k_rrf: int = 60) -> list[str]:
        pts: dict[int, float] = {}
        for ranking in (_topk(sims, tope), _topk(sc_bm25, tope)):
            for rango, doc in enumerate(ranking):
                pts[doc] = pts.get(doc, 0.0) + 1.0 / (k_rrf + rango)
        mejores = sorted(pts, key=pts.get, reverse=True)[:k]
        return self.codigos[mejores].tolist()

    def hibrido(self, texto: str, k: int = 20, **kw) -> list[str]:
        v = self.embed_consulta(texto)
        return self.rrf_desde(self.emb @ v, self.bm25_scores(texto), k, **kw)

    # --- por frases: consulta cada frase del caso y fusiona (RRF) ---
    def candidatos(
        self,
        frases: list[str],
        emb_frases: np.ndarray,
        k: int = 100,
        k_frase: int = 15,
        usar_bm25: bool = True,
    ) -> list[str]:
        """Pool ordenado de códigos candidatos para un caso.

        frases: frases del caso. emb_frases: sus embeddings (n_frases, DIMS), L2.
        Por cada frase se toma el top-`k_frase` denso (y BM25 si `usar_bm25`); todas
        esas listas se fusionan por RRF y se devuelve el top-`k`.
        """
        rankings: list[np.ndarray] = []
        for v in emb_frases:
            rankings.append(_topk(self.emb @ v, k_frase))
        if usar_bm25:
            for f in frases:
                rankings.append(_topk(self.bm25_scores(f), k_frase))
        return self.codigos[rrf(rankings, k)].tolist()
