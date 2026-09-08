"""Genera notebooks/analisis.ipynb a partir de los resultados ya calculados.

    python notebooks/_generar_notebook.py

El notebook solo lee resultados/ y figuras/, no vuelve a llamar a la API.
"""

from pathlib import Path

import nbformat as nbf

RAIZ = Path(__file__).resolve().parent.parent
nb = nbf.v4.new_notebook()
c = []


def md(t):
    c.append(nbf.v4.new_markdown_cell(t.strip()))


def code(t):
    c.append(nbf.v4.new_code_cell(t.strip()))


md("""
# Codificación clínica CIE-10 con recuperación + LLM: análisis

Cuaderno de lectura del estudio. Todos los números salen de los archivos de
`resultados/`; las corridas contra la API están en los scripts de `src/`.

**Resultado principal:** en CodiEsp-D, `gpt-4o-mini` + recuperación llega a **MAP 0,090**
en test (categoría de 3 caracteres: 0,267). El mejor sistema supervisado del shared task
de 2020 llegó a 0,593.
""")

code("""
import json, pandas as pd
from pathlib import Path
RES = Path("..") / "resultados"
FIG = Path("..") / "figuras"
pd.set_option("display.max_colwidth", 90)
""")

md("## 1. El corpus (Bloque A)")
code("""
print((RES / "eda_bloque_a.md").read_text())
""")

md("""
## 2. La recuperación tiene un techo (Bloque B)

Consultar con el caso completo fracasa. Por frases y con fusión denso + BM25 sube, pero
la unión de todos los candidatos solo cubre el 52% del gold: el 65% de lo que falta son
códigos vagos sin anclaje textual.
""")
code("""
from IPython.display import Image, display
display(Image(str(FIG / "fig_recall_retrieval.png")))
print((RES / "eval_retrieval_dev.md").read_text())
""")

md("## 3. El codificador y los ablations (Bloques C y D)")
code("""
filas = [json.loads(l) for l in (RES / "eval_codificador.jsonl").read_text().splitlines() if l.strip()]
df = pd.DataFrame(filas)[["config","n","MAP","MAP_cat3","F1_micro","P","R",
                          "cods_pred/caso","alucinac/caso","costo_1000casos_usd"]]
df
""")
code("""
display(Image(str(FIG / "fig_map_por_config.png")))
display(Image(str(FIG / "fig_costo_map.png")))
""")

md("""
Lecturas:

- **Candidatos vs. sin candidatos:** el MAP exacto casi no cambia, pero la alucinación
  de códigos cae de 0,39 a 0,05 por caso. La recuperación ancla, no mejora la exactitud.
- **Prompt exhaustivo vs. mínimo:** el mínimo predice 6 códigos por caso (el gold tiene
  ~13) y el MAP baja a 0,069.
- **Few-shot:** neutro.
- **gpt-4o vs. gpt-4o-mini:** dobla el MAP, a ~19x el costo por caso.
""")

md("## 4. Análisis de errores")
code("""
display(Image(str(FIG / "fig_destino_gold.png")))
print((RES / "analisis_errores_gpt-4o-mini_concand.md").read_text())
""")

md("""
## 5. Conclusión

Un LLM genérico sin entrenar queda lejos del estado del arte supervisado en
codificación exhaustiva CIE-10-ES, y la brecha es estructural, no de "más datos":

1. La recuperación sobre descripciones no puede pasar de ~0,52 de recall.
2. El 37% del gold son códigos administrativos vagos sin anclaje textual.
3. La mitad de los fallos clínicos son de especificidad (categoría correcta, dígito
   equivocado): a nivel de 3 caracteres el acierto casi se duplica.

Como apoyo acotado, con validación encima y sobre la parte nombrable del diagnóstico, la
herramienta sí tiene dónde aportar. Ese es el punto de partida de las fases siguientes.
""")

nb["cells"] = c
nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
salida = RAIZ / "notebooks" / "analisis.ipynb"
nbf.write(nb, salida)
print("escrito", salida.relative_to(RAIZ))
