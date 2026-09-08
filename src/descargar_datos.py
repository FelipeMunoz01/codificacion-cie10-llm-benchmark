"""Descarga el corpus CodiEsp y la lista de códigos válidos en data/codiesp/.

    python src/descargar_datos.py

Fuentes (Zenodo, CC-BY 4.0):
  - corpus v4 (train/dev/test con gold + background): record 3837305
  - lista de códigos CIE-10-ES 2018 (D y P): record 3706838
"""

from __future__ import annotations

import io
import sys
import urllib.request
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "data" / "codiesp"

RECURSOS = {
    "corpus": ("https://zenodo.org/records/3837305/files/codiesp.zip?download=1",
               "0642277ab2e7234f7053316b57c5e28c"),
    "codigos": ("https://zenodo.org/records/3706838/files/codiesp_codes.zip?download=1",
                "531d29c58447e86820517a5a0c437a2d"),
}


def _bajar_y_extraer(url: str, destino: Path) -> None:
    print(f"descargando {url.split('/')[-1].split('?')[0]} ...")
    with urllib.request.urlopen(url) as r:
        datos = r.read()
    with zipfile.ZipFile(io.BytesIO(datos)) as z:
        z.extractall(destino)
    print(f"  extraído en {destino.relative_to(RAIZ)}")


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    for nombre, (url, _md5) in RECURSOS.items():
        _bajar_y_extraer(url, DESTINO)
    hay_corpus = (DESTINO / "final_dataset_v4_to_publish" / "train" / "trainD.tsv").exists()
    hay_codigos = (DESTINO / "codiesp_codes" / "codiesp-D_codes.tsv").exists()
    if hay_corpus and hay_codigos:
        print("\nlisto. data/codiesp/ tiene el corpus y la lista de códigos.")
    else:
        print("\nalgo falta, revisa data/codiesp/", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
