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

`FASE 1 - Bloque A completo (1.1 a 1.4). Siguiente: Bloque B (índice de recuperación).`

Hallazgos de Bloque A (detalle en `resultados/eda_bloque_a.md`):
- 500 / 250 / 250 casos (train / dev / test), ~11 códigos de diagnóstico por caso,
  textos de ~350 palabras.
- CodiEsp-D es multietiqueta a nivel de caso, sin principal vs secundario (ver DECISIONES).
- Diccionario CIE-10-ES: 98.288 códigos, cobertura del gold 100%.
- Solo el 62% de los códigos de test aparece en train: argumento fuerte para el enfoque
  RAG + LLM sin entrenamiento, que no depende de haber visto antes el código.

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

- [ ] **1.5 Normalizar el diccionario.** Una fila por código: `codigo`, `descripcion`,
  `notas` (incluye/excluye), `categoria_padre`.
  *Listo cuando:* hay un parquet limpio del diccionario.
- [ ] **1.6 Generar embeddings del diccionario** (una sola vez) y guardarlos en un índice
  local (FAISS o Chroma).
  *Listo cuando:* el índice se carga desde disco y responde consultas.
- [ ] **1.7 Búsqueda densa.** Función `texto -> top-k códigos candidatos`.
  *Listo cuando:* devuelve k candidatos razonables para 5 textos de ejemplo.
- [ ] **1.8 Búsqueda léxica BM25 + fusión.** Añadir BM25 y una función que combine ambas
  listas (híbrida).
  *Listo cuando:* la función híbrida devuelve una lista fusionada y ordenada.
- [ ] **1.9 Evaluar SOLO el retrieval.** `recall@k` (¿está el código correcto entre los k?)
  para k = 5, 10, 20, 50. Este número es el techo de todo lo que sigue.
  *Listo cuando:* hay una tabla recall@k para denso, léxico e híbrido.

### Bloque C: El codificador (LLM)

- [ ] **1.10 Diseñar el prompt.** Entrada: texto + candidatos. Salida: JSON con diagnóstico
  principal, secundarios y la frase del texto que justifica cada uno.
  *Listo cuando:* el prompt está en un archivo versionado, no suelto en el notebook.
- [ ] **1.11 Salida estructurada.** Esquema Pydantic + parser con reintentos si el JSON
  viene mal formado.
  *Listo cuando:* 20 llamadas seguidas devuelven objetos válidos.
- [ ] **1.12 Función end-to-end.** `caso -> retrieval -> LLM -> lista de códigos predichos`.
  *Listo cuando:* corre sobre 1 caso y devuelve códigos con justificación.
- [ ] **1.13 Iterar el prompt a mano** con 10 a 20 casos.
  *Listo cuando:* el output se ve estable y sensato en esos casos.

### Bloque D: Evaluación (el núcleo del proyecto)

- [ ] **1.14 Métricas CodiEsp.** Precisión, recall, F1 a nivel de código y MAP. Manejar
  bien los códigos parciales (3 vs 4-5 caracteres).
  *Listo cuando:* las métricas reproducen el formato oficial de CodiEsp sobre un ejemplo.
- [ ] **1.15 Corrida base sobre dev completo.** Obtener el primer número honesto.
  *Listo cuando:* hay un F1 base guardado en `resultados/`.
- [ ] **1.16 Ablations** (cada uno = una corrida y una fila de tabla):
  - [ ] solo LLM sin retrieval
  - [ ] retrieval denso vs híbrido
  - [ ] k = 10 vs 20 vs 50 candidatos
  - [ ] prompt mínimo vs prompt con reglas del cuaderno NotebookLM
  - [ ] modelo LLM barato vs mediano
  *Listo cuando:* hay una tabla comparativa completa.
- [ ] **1.17 Análisis de errores.** Revisar 30 casos fallados, clasificar el tipo de error
  (3 vs 4 caracteres, categoría rara, confusión principal/secundario, alucinación de
  código inexistente), tabla resumen.
  *Listo cuando:* hay una tabla de tipos de error con conteos y ejemplos.
- [ ] **1.18 Corrida final sobre test** (UNA sola vez) con la mejor configuración.
  Comparar honesto con el leaderboard de CodiEsp.
  *Listo cuando:* hay un número de test y un párrafo de comparación con la literatura.
- [ ] **1.19 Costo y latencia** por caso, proyección a escala (codificar N epicrisis).
  *Listo cuando:* hay una estimación en pesos y segundos por caso.

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
