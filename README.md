# Asistente de codificación clínica CIE-10 con recuperación + LLM, evaluado

> Estudio de benchmark sobre datos públicos (CodiEsp). No es un producto: es una
> medición honesta de qué tan lejos está un LLM moderno del estado del arte supervisado
> en codificación clínica automática en español, y de qué aporta (y qué no) añadirle
> recuperación.

Dado el texto de un caso clínico en español, el sistema propone los códigos de
diagnóstico CIE-10-ES del episodio: recupera códigos candidatos del catálogo oficial y
un LLM elige y justifica, pudiendo además proponer códigos que la recuperación no
alcanza. Todo lo que emite el LLM se valida contra los 98.288 códigos válidos.

## El hallazgo principal

En CodiEsp-D (predecir el conjunto de códigos de diagnóstico de cada caso), el mejor
sistema del shared task de 2020, con fine-tuning supervisado, alcanzó **MAP 0,593**.

Este proyecto, sin entrenar nada:

| configuración | MAP exacto | MAP categoría (3 car.) | alucinación/caso | costo/1000 casos |
|---|---|---|---|---|
| gpt-4o-mini + recuperación (dev) | `{DEV_MINI_MAP}` | `{DEV_MINI_MAP3}` | `{DEV_MINI_ALUC}` | USD `{DEV_MINI_COSTO}` |
| gpt-4o + recuperación (dev, 50 casos) | `{DEV_4O_MAP}` | `{DEV_4O_MAP3}` | `{DEV_4O_ALUC}` | USD `{DEV_4O_COSTO}` |
| gpt-4o-mini + recuperación (**test**) | `{TEST_MAP}` | `{TEST_MAP3}` | `{TEST_ALUC}` | USD `{TEST_COSTO}` |

La distancia con el SOTA supervisado es grande y real. El valor del proyecto está en
explicar de qué está hecha esa distancia.

## De qué está hecha la distancia

1. **La recuperación tiene un techo de ~0,52.** Consultar con el caso completo fracasa
   (un caso tiene ~11 diagnósticos y un embedding no los representa). Por frases y con
   fusión denso + BM25 sube, pero la unión total de candidatos solo cubre el 52% del
   gold. El 65% de lo que falta son códigos vagos ("no especificado", "NEOM", "otros
   trastornos de...") que no tienen anclaje textual y no se pueden recuperar por
   similitud.

2. **Por eso la recuperación no es una lista cerrada.** El LLM puede proponer códigos
   fuera de los candidatos con su propio conocimiento de CIE-10. Aun así:

3. **La recuperación casi no mueve el MAP exacto, pero sí ancla.** Con candidatos vs.
   sin candidatos el MAP exacto es casi igual, pero las alucinaciones caen de
   `{ALUC_SIN}` a `{ALUC_CON}` por caso y mejora la especificidad (MAP categoría
   `{MAP3_CON}` vs `{MAP3_SIN}`). Su aporte es fiabilidad, no exactitud.

4. **El prompt exhaustivo es decisivo.** Un prompt escueto hace que el modelo prediga
   ~6 códigos por caso (el gold tiene ~13) y el recall se hunde. Instruirlo a codificar
   síntomas, consumo de tabaco/alcohol, antecedentes y variantes "no especificado" sube
   el MAP de `{MAP_MIN}` a `{MAP_CONCAND}`.

5. **La mitad de los fallos exactos son de especificidad, no de criterio clínico.** El
   MAP por categoría de 3 caracteres casi dobla al exacto: el modelo identifica bien el
   cuadro (`N20`, cálculo urinario) pero elige el dígito equivocado (`N20.1` en vez de
   `N20.0`).

6. **El tamaño del modelo domina.** gpt-4o casi dobla el MAP de gpt-4o-mini, a 14 veces
   el costo.

## Metodología

- **Datos:** corpus CodiEsp (500 / 250 / 250 casos train / dev / test con gold), y la
  lista oficial de 98.288 códigos CIE-10-ES de diagnóstico. Loaders en `src/datos.py`.
- **Recuperación** (`src/recuperar.py`): el caso se parte en frases; por cada frase se
  toman los códigos más cercanos por embeddings (`text-embedding-3-small`, dim 512) y
  por BM25 (matriz dispersa); las listas se fusionan con RRF. Expansión de abreviaturas
  clínicas frecuentes (HTA, DM2, ITU...).
- **Codificador** (`src/codificador.py`): el LLM recibe el caso y los ~150 candidatos
  con su descripción, y devuelve JSON estructurado (código + evidencia). Validación
  contra el catálogo, resolución de códigos sin punto, reintentos ante límite de tasa.
- **Evaluación** (`src/eval_codificador.py`): MAP (métrica oficial de CodiEsp-D), P/R/F1
  micro exacto y por categoría de 3 caracteres, tasa de alucinación, costo y latencia.
  Ablations: con/sin candidatos, prompt exhaustivo/mínimo, zero/few-shot, mini/4o.

## Limitaciones

- CodiEsp-D es dato clínico de España (CIE-10-ES ≈ ICD-10-CM). El sistema de Chile usa
  CIE-10 OMS para diagnósticos y CIE-9-MC para procedimientos: la arquitectura se
  reusa cambiando el catálogo indexado, no el pipeline.
- No se distingue diagnóstico principal de secundarios porque el gold de CodiEsp-D no
  lo etiqueta.
- La lista oficial de códigos no trae notas de inclusión/exclusión ni jerarquía, que
  ayudarían a la recuperación.
- Evaluación sobre 250 casos de test: los intervalos de confianza no son estrechos.

## Herramientas

Python, pandas, numpy, scikit-learn, scipy (BM25 disperso), OpenAI API (LLM y
embeddings), matplotlib.

## Cómo reproducir

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # y completar OPENAI_API_KEY

# descargar CodiEsp (corpus + lista de códigos) en data/codiesp/  (ver src/datos.py)
python src/indice.py              # embeddings del catálogo (~USD 0,06, una vez)
python src/eval_retrieval.py --split dev
python src/eval_codificador.py --split dev --n 250
python src/analisis_errores.py --config gpt-4o-mini_concand --split dev
python src/figuras.py
```

## Fuentes de datos

- **CodiEsp corpus** (CLEF eHealth 2020), Barcelona Supercomputing Center. Zenodo
  3837305, CC-BY 4.0.
- **CodiEsp code list** (CIE-10-ES 2018). Zenodo 3706838, CC-BY 4.0.
