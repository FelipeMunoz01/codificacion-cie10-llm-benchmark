"""Bloque A, paso 1.4: exploración del corpus CodiEsp (subtrack D, diagnósticos).

Imprime un resumen y lo guarda en resultados/eda_bloque_a.md.
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

from datos import cargar_casos, cargar_diccionario, cargar_gold

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "resultados" / "eda_bloque_a.md"


def _pct(x, total):
    return f"{100 * x / total:.1f}%"


def main() -> None:
    buf = io.StringIO()

    def p(*args):
        linea = " ".join(str(a) for a in args)
        print(linea)
        buf.write(linea + "\n")

    p("# EDA Bloque A - CodiEsp subtrack D (diagnósticos)\n")

    # --- Casos por split ---
    casos = {s: cargar_casos(s) for s in ("train", "dev", "test")}
    gold = {s: cargar_gold(s, "D") for s in ("train", "dev", "test")}

    p("## Casos y códigos por split\n")
    p("| split | casos | filas gold | códigos/caso (media) | mediana | min | max |")
    p("|---|---|---|---|---|---|---|")
    for s in ("train", "dev", "test"):
        por_caso = gold[s].groupby("id").size()
        p(
            f"| {s} | {len(casos[s])} | {len(gold[s])} | "
            f"{por_caso.mean():.1f} | {por_caso.median():.0f} | "
            f"{por_caso.min()} | {por_caso.max()} |"
        )

    # --- Longitud de los textos ---
    p("\n## Longitud de los casos (palabras)\n")
    p("| split | media | p10 | p50 | p90 | max |")
    p("|---|---|---|---|---|---|")
    for s in ("train", "dev", "test"):
        w = casos[s]["n_palabras"]
        p(
            f"| {s} | {w.mean():.0f} | {w.quantile(.1):.0f} | {w.quantile(.5):.0f} | "
            f"{w.quantile(.9):.0f} | {w.max()} |"
        )

    # --- Diccionario y cobertura ---
    dicc = cargar_diccionario("D")
    codigos_dicc = set(dicc["codigo"])
    p(f"\n## Diccionario CIE-10-ES (subtrack D)\n")
    p(f"- Códigos en el diccionario: {len(codigos_dicc):,}")

    p("\n### Cobertura del gold por el diccionario\n")
    p("| split | códigos únicos gold | en diccionario | fuera | cobertura |")
    p("|---|---|---|---|---|")
    fuera_total = set()
    for s in ("train", "dev", "test"):
        u = set(gold[s]["codigo"])
        dentro = u & codigos_dicc
        fuera = u - codigos_dicc
        fuera_total |= fuera
        p(f"| {s} | {len(u)} | {len(dentro)} | {len(fuera)} | {_pct(len(dentro), len(u))} |")
    if fuera_total:
        p(f"\nEjemplos de códigos gold fuera del diccionario: {sorted(fuera_total)[:20]}")
    else:
        p("\nTodos los códigos gold están en el diccionario.")

    # --- Solapamiento de códigos entre splits ---
    u_train = set(gold["train"]["codigo"])
    p("\n## Códigos de dev/test ya vistos en train\n")
    p("| split | códigos únicos | también en train | solo en este split | vistos |")
    p("|---|---|---|---|---|")
    for s in ("dev", "test"):
        u = set(gold[s]["codigo"])
        vistos = u & u_train
        p(f"| {s} | {len(u)} | {len(vistos)} | {len(u - u_train)} | {_pct(len(vistos), len(u))} |")

    # --- Distribución por longitud/especificidad del código ---
    p("\n## Especificidad de los códigos gold (nº de caracteres alfanuméricos)\n")
    def nchars(c):
        return len(c.replace(".", ""))
    p("| split | 3 (categoría) | 4 | 5 | 6+ |")
    p("|---|---|---|---|---|")
    for s in ("train", "dev", "test"):
        u = pd.Series(sorted(set(gold[s]["codigo"])))
        n = u.map(nchars)
        p(f"| {s} | {(n == 3).sum()} | {(n == 4).sum()} | {(n == 5).sum()} | {(n >= 6).sum()} |")

    # --- Códigos más frecuentes en train ---
    p("\n## 15 códigos de diagnóstico más frecuentes en train\n")
    top = gold["train"]["codigo"].value_counts().head(15)
    desc = dicc.set_index("codigo")["desc_es"].to_dict()
    p("| código | casos | descripción |")
    p("|---|---|---|")
    for cod, n in top.items():
        p(f"| {cod} | {n} | {desc.get(cod, '(no está en el diccionario)')[:70]} |")

    SALIDA.parent.mkdir(exist_ok=True)
    SALIDA.write_text(buf.getvalue(), encoding="utf-8")
    p(f"\n---\nGuardado en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
