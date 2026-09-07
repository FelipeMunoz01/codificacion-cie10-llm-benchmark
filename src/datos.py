"""Carga del corpus CodiEsp y de la lista oficial de códigos CIE-10-ES.

Estructura esperada en disco (no versionada, ver .gitignore):

    data/codiesp/final_dataset_v4_to_publish/{train,dev,test}/
        text_files/<id>.txt          casos clínicos en español
        {train,dev,test}D.tsv        gold de diagnósticos: id <TAB> codigo
        {train,dev,test}P.tsv        gold de procedimientos: id <TAB> codigo
        {train,dev,test}X.tsv        id <TAB> tipo <TAB> codigo <TAB> texto_ref <TAB> posicion
    data/codiesp/codiesp_codes/
        codiesp-D_codes.tsv          codigo <TAB> desc_es <TAB> desc_en   (98.288 diagnósticos)
        codiesp-P_codes.tsv          codigo <TAB> desc_es <TAB> desc_en   (87.170 procedimientos)

Convención: todos los códigos se normalizan a minúsculas, igual que el script de
evaluación oficial de CodiEsp.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DIR_CORPUS = RAIZ / "data" / "codiesp" / "final_dataset_v4_to_publish"
DIR_CODIGOS = RAIZ / "data" / "codiesp" / "codiesp_codes"

SPLITS = ("train", "dev", "test")


def _norm_codigo(serie: pd.Series) -> pd.Series:
    return serie.astype(str).str.strip().str.lower()


def cargar_casos(split: str) -> pd.DataFrame:
    """Devuelve un DataFrame con columnas: id, texto, n_palabras, n_caracteres."""
    if split not in SPLITS:
        raise ValueError(f"split debe ser uno de {SPLITS}, no {split!r}")
    dir_textos = DIR_CORPUS / split / "text_files"
    filas = []
    for archivo in sorted(dir_textos.glob("*.txt")):
        texto = archivo.read_text(encoding="utf-8")
        filas.append(
            {
                "id": archivo.stem,
                "texto": texto,
                "n_palabras": len(texto.split()),
                "n_caracteres": len(texto),
            }
        )
    return pd.DataFrame(filas)


def cargar_gold(split: str, subtrack: str = "D") -> pd.DataFrame:
    """Anotaciones gold de un subtrack ('D' diagnósticos, 'P' procedimientos).

    Devuelve columnas: id, codigo. Una fila por par (caso, código).
    """
    subtrack = subtrack.upper()
    if subtrack not in ("D", "P"):
        raise ValueError("subtrack debe ser 'D' o 'P'")
    ruta = DIR_CORPUS / split / f"{split}{subtrack}.tsv"
    df = pd.read_csv(ruta, sep="\t", header=None, names=["id", "codigo"], dtype=str)
    df["codigo"] = _norm_codigo(df["codigo"])
    return df.drop_duplicates().reset_index(drop=True)


def cargar_spans(split: str) -> pd.DataFrame:
    """Subtrack X: referencias textuales de cada código.

    Columnas: id, tipo (DIAGNOSTICO/PROCEDIMIENTO), codigo, texto_ref, posicion.
    """
    ruta = DIR_CORPUS / split / f"{split}X.tsv"
    df = pd.read_csv(
        ruta,
        sep="\t",
        header=None,
        names=["id", "tipo", "codigo", "texto_ref", "posicion"],
        dtype=str,
    )
    df["codigo"] = _norm_codigo(df["codigo"])
    return df


def cargar_diccionario(subtrack: str = "D") -> pd.DataFrame:
    """Lista oficial de códigos válidos CIE-10-ES 2018.

    Columnas: codigo, desc_es, desc_en.
    """
    subtrack = subtrack.upper()
    nombre = {"D": "codiesp-D_codes.tsv", "P": "codiesp-P_codes.tsv"}[subtrack]
    df = pd.read_csv(
        DIR_CODIGOS / nombre,
        sep="\t",
        header=None,
        names=["codigo", "desc_es", "desc_en"],
        dtype=str,
    )
    df["codigo"] = _norm_codigo(df["codigo"])
    for col in ("desc_es", "desc_en"):
        df[col] = df[col].astype(str).str.strip()
    return df.drop_duplicates(subset="codigo").reset_index(drop=True)
