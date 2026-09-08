# Roadmap: Asistente de codificación CIE-10 / CIE-9-MC con RAG + LLM, evaluado

Proyecto de portafolio (y base de un posible servicio) para asistir la codificación
clínica bajo el modelo IR-GRD de Chile. La idea central no es "chatear con documentos",
sino **construir un sistema de recuperación + LLM y medir qué tan bien codifica** contra
un benchmark público, con análisis de errores y ablations.

## Principio de trabajo: método del equilibrio

- **Público** (repo portafolio): el método, el harness de evaluación, las tablas de
  resultados, el análisis de errores, la arquitectura, y una demo **solo sobre datos
  públicos (CodiEsp)**. Licencia MIT, es la versión didáctica a propósito.
- **Privado** (repo producto): el motor de reglas completo, los prompts afinados, la
  lógica GRD chilena (severidad CC/MCC, agrupación), la capa de datos sensibles y todo
  trabajo con clientes. Sin licencia, todos los derechos reservados.

## Estado actual

`FASE 1 - Bloques A-D completos. Falta el entregable (1.20-1.24): notebook y repo público.`

Resultados finales (`resultados/`, figuras en `figuras/`):
- **test 250, gpt-4o-mini + candidatos: MAP 0,090 exacto / 0,267 categoría** (dev: 0,092
  / 0,274, coincide). SOTA supervisado 2020: 0,593.
- gpt-4o (dev, 50): MAP 0,196 exacto / 0,366 categoría, ~19x el costo.
- Candidatos: casi no mueven el MAP exacto, pero alucinación 0,39 -> 0,05/caso.
- Prompt mínimo: MAP 0,069 (subcodifica: 6 códigos/caso vs gold 13). Few-shot: neutro.
- Reparto del gold: 16% exacto, 19,5% categoría correcta, 37% códigos vagos sin
  anclaje, 22% otros no recuperados, 6% estaba en candidatos y no se eligió.

Hallazgos de Bloque A (`resultados/eda_bloque_a.md`):
- 500 / 250 / 250 casos, ~11 códigos de diagnóstico por caso, textos ~350 palabras.
- CodiEsp-D es multietiqueta a nivel de caso, sin principal vs secundario.
- Diccionario CIE-10-ES: 98.288 códigos, cobertura del gold 100%.
- Solo el 62% de los códigos de test aparece en train.

Hallazgos de Bloque B (`resultados/eval_retrieval_dev.md`):
- Consulta por frases + híbrido: recall@200 ≈ 0,31; techo de la unión 0,52.
- El 65% del gold no recuperado son códigos vagos sin anclaje textual.
- **Diseño revisado**: la recuperación da pistas, no una lista cerrada. El LLM puede
  proponer códigos fuera de las pistas y todo se valida contra los 98.288 válidos.
  Ablation obligatorio: LLM solo vs LLM + candidatos (ver DECISIONES).

Marca cada casilla al terminar. "Listo cuando" define el criterio de término de cada paso.

---

## FASE 0 - Preparación y decisiones (sin código todavía)

- [x] **0.1 Nombre del repo público.** `asistente-codificacion-clinica-cie10`.
- [x] **0.2 Estructura de dos repos.** Definida en `DECISIONES.md`.
- [x] **0.3 Alcance de Fase 1 por escrito.** Cerrado en `DECISIONES.md`.
- [x] **0.4 Proveedor de LLM y de embeddings.** OpenAI (`gpt-4o-mini` + `gpt-4o`;
  `text-embedding-3-small` + `-large`), embeddings por API, tope USD 25 a 30.
  *Falta:* crear la cuenta OpenAI, cargar crédito y probar la key con una llamada.
- [x] **0.5 Entorno de trabajo.** Estructura de carpetas, `requirements.txt`,
  `.gitignore`, `.env` con la key validada (HTTP 200), `venv` en `.venv/` con todo
  instalado. Sin `faiss-cpu` (ver DECISIONES.md).
- [x] **0.6 Primer commit.** `git init` en `proyecto 7/`, rama `main`, commit `9780c88`
  sin `Co-Authored-By`. Repo local, sin GitHub todavía.

---

## FASE 1 - Diagnóstico principal CIE-10 desde texto, medido en CodiEsp

### Bloque A: Datos

- [x] **1.1 Descargar CodiEsp.** Corpus v4 (Zenodo 3837305, incluye test con gold) +
  lista de códigos válidos (Zenodo 3706838). En `data/codiesp/`, git lo ignora.
- [x] **1.2 Cargar a pandas.** Loaders en `src/datos.py`: `cargar_casos`, `cargar_gold`,
  `cargar_spans`, `cargar_diccionario`. Conteos cuadran con la doc (1000 casos).
- [x] **1.3 Diccionario.** El `CIE-10.xlsx` OMS no sirve (ver DECISIONES). Se usa la lista
  oficial CIE-10-ES de CodiEsp. Cobertura del gold: 100%.
- [x] **1.4 EDA.** `src/eda_bloque_a.py` → `resultados/eda_bloque_a.md`. Falta pasar los
  gráficos al notebook (paso 1.20).

### Bloque B: Base de conocimiento e índice de recuperación

- [x] **1.5 Normalizar el diccionario.** `src/indice.py`: una fila por código
  (`codigo`, `desc_es`, `texto`). El fichero de códigos válidos no trae jerarquía ni
  notas incluye/excluye, así que el documento indexado es "CÓDIGO: descripción".
- [x] **1.6 Embeddings del diccionario.** `text-embedding-3-small` dim 512, 98.288
  vectores, ~3 min, ~USD 0,06. En `data/index/` (no versionado, manifiesto sí).
- [x] **1.7 Búsqueda densa.** `Recuperador.denso` (numpy, coseno). OK en consultas
  cortas ("cálculo del riñón" -> N20.0).
- [x] **1.8 BM25 disperso + fusión RRF.** `_BM25Disperso` (scipy sparse; `rank_bm25`
  era 80x más lento). `Recuperador.hibrido` y `.candidatos` (por frases).
- [x] **1.9 Evaluar el retrieval.** `src/eval_retrieval.py` ->
  `resultados/eval_retrieval_dev.md`. Techo de recuperación ~0,52; ver diseño revisado.

### Bloque C: El codificador (LLM)

- [x] **1.10 Prompt** en `src/codificador.py` (`SISTEMA`), versionado. Salida JSON con
  código + evidencia textual. Variante `SISTEMA_MIN` para el ablation.
- [x] **1.11 Salida estructurada.** `response_format` json_schema estricto + validación
  contra los 98.288 códigos válidos + resolución de códigos sin punto + retry 429.
- [x] **1.12 Función end-to-end.** `Codificador.codificar(texto, candidatos)`.
- [x] **1.13 Iteración del prompt.** Prompt exhaustivo (síntomas, tabaco, Z-codes,
  "no especificado") tras ver que el mínimo subcodifica.

### Bloque D: Evaluación (el núcleo del proyecto)

- [x] **1.14 Métricas.** `src/eval_codificador.py`: MAP (oficial CodiEsp-D), P/R/F1
  micro exacto y por categoría de 3 caracteres, alucinación, coste. Cache de predicciones.
- [x] **1.15 Corrida base dev.** gpt-4o-mini con candidatos. En `resultados/`.
- [x] **1.16 Ablations** (`resultados/eval_codificador.jsonl`):
  - [x] LLM solo (sin candidatos) vs con candidatos
  - [x] prompt exhaustivo vs prompt mínimo
  - [x] few-shot vs zero-shot
  - [x] gpt-4o-mini vs gpt-4o
  - [~] denso vs híbrido / k candidatos: cubierto en `eval_retrieval` (Bloque B)
- [x] **1.17 Análisis de errores.** `src/analisis_errores.py` ->
  `resultados/analisis_errores_gpt-4o-mini_concand.md`.
- [x] **1.18 Corrida final sobre test.** MAP 0,090; coincide con dev; comparación con el
  SOTA supervisado en el README.
- [x] **1.19 Costo y latencia.** En el jsonl y en `figuras/fig_costo_map.png`.

### Bloque E: Entregable de Fase 1

- [ ] **1.20 Notebook de análisis** con todas las tablas y gráficos.
- [ ] **1.21 README público** en el estilo de siempre (descripción, método, hallazgos,
  limitaciones, nota de "versión didáctica sobre datos públicos").
- [ ] **1.22 Limpiar `src/`.** Dejar el motor de reglas como interfaz / stub con nota
  "implementación completa en versión privada".
- [ ] **1.23 Publicar el repo público** (CodiEsp only) con el flujo de GitHub habitual.
- [ ] **1.24 Writeup corto para LinkedIn** con la tabla de resultados.

---

## FASE 2 - Procedimientos CIE-9-MC + capa de reglas determinista (parcialmente privado)

- [ ] **2.1** Preparar el diccionario CIE-9-MC de procedimientos, indexar igual que Fase 1.
- [ ] **2.2** Extender el codificador a procedimiento principal + secundarios.
- [ ] **2.3** Evaluar procedimientos en el track de procedimientos de CodiEsp.
- [ ] **2.4** Implementar la capa de reglas como funciones Python puras sobre la salida:
  - [ ] pasos integrantes / no fragmentar
  - [ ] vía de acceso inherente (omitir o añadir según el descriptor oficial)
  - [ ] códigos de combinación / anti-unbundling
  - [ ] excepciones (respaldo por imagen, doble codificación por técnica)
- [ ] **2.5** Evaluar con y sin capa de reglas: ¿mejora el F1?, ¿en qué subgrupo?
- [ ] **2.6** Análisis de errores de procedimientos.
- [ ] **2.7** Actualizar notebook y README (esto ya vive mayormente en el repo privado).

---

## FASE 3 - Análisis GRD / auditoría (privado)

- [ ] **3.1** Mapear códigos a GRD con la lógica IR-GRD y las tablas maestras MINSAL.
- [ ] **3.2** Clasificar diagnósticos secundarios como CC / MCC y nivel de severidad 1 a 4.
- [ ] **3.3** Alertas de auditoría (documentación faltante, incoherencia diagnóstico
  vs procedimiento).
- [ ] **3.4** Generar el "resumen sugerido para el registro" (párrafo técnico copiable).
- [ ] **3.5** Validar contra el parquet GRD real (si trae texto) o contra casos sintéticos.

---

## FASE 4 - Capa de datos sensibles y despliegue (privado, solo si va a producto)

- [ ] **4.1** Detector de RUT (regex + dígito verificador) y de nombres (NER en español),
  medir recall con un set de RUTs y nombres inyectados.
- [ ] **4.2** Abstraer el backend del LLM tras una interfaz (API o modelo local
  intercambiable con un cambio de configuración).
- [ ] **4.3** Demo Streamlit: pegar epicrisis anonimizada, ver códigos + justificación
  + alertas.
- [ ] **4.4** Probar con un modelo local en GPU arrendada, medir diferencia de calidad
  vs API.
- [ ] **4.5** Documentar la arquitectura on-premise para clientes (el dato no sale de
  la red).

---

## FASE 5 - Difusión y oferta de servicio

- [ ] **5.1** Pinear el repo público, actualizar el perfil de GitHub.
- [ ] **5.2** Artículo / post con los resultados y el enfoque de evaluación.
- [ ] **5.3** Una página de servicio: qué hace, qué mide, cómo se despliega en privado.

---

## Candidatos de nombre para el repo público

- `codificacion-clinica-cie10-rag`
- `asistente-codificacion-cie10-grd`
- `rag-codificacion-cie10-chile`
- `evaluacion-codificacion-clinica-llm`

## Fuentes de referencia (todas de acceso abierto)

- CodiEsp corpus + paper de resumen: Zenodo y actas CEUR-WS de CLEF eHealth 2020.
- Papers de equipos participantes: mismo volumen CEUR, descarga libre.
- Modelos clínicos en español: Barcelona Supercomputing Center en HuggingFace
  (`bsc-bio-ehr-es` y similares).
- Documentación oficial CIE-10-OMS y CIE-9-MC del MINSAL.
