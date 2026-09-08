# Decisiones del proyecto

Registro de decisiones tomadas, con su fecha y el motivo. Igual que en proyecto5.

---

## 2026-09-06 · Fase 0

### 0.1 Nombre del repo público

**`codificacion-cie10-llm-benchmark`** (renombrado tras cerrar Fase 1: el README quedó
como estudio de benchmark, no como asistente/servicio).

- CodiEsp es dato clínico de España, así que se evita "chile" en el nombre del repo
  público. Lo específico de Chile (IR-GRD, MINSAL) vive en el repo privado.

### 0.2 Estructura de dos repos (método del equilibrio)

**Público** (`proyecto 7` en el disco → repo GitHub, licencia MIT):

- Pipeline completo de Fase 1 sobre CodiEsp: ingesta, índice, retrieval denso + BM25,
  codificador LLM, métricas, ablations, análisis de errores.
- Prompt base / mínimo, versión genérica.
- Notebook de análisis, README, `requirements.txt`, `.gitignore`.
- Motor de reglas como interfaz vacía (stub) + 2 o 3 reglas de ejemplo documentadas.
- El índice de embeddings ya calculado (para reproducibilidad).

**Privado** (repo producto, sin licencia, todos los derechos reservados):

- Set completo de reglas de auditoría (las ~30 del NotebookLM) ya implementadas.
- Prompts de producción afinados.
- Lógica IR-GRD chilena: mapeo a GRD, severidad CC / MCC, niveles 1 a 4.
- Capa de detección de PII (RUT, nombres) en versión de producción.
- Config de despliegue on-premise, material de clientes.
- Cualquier dato derivado de GRD real que no sea estadística agregada.

**Nunca al repo público:** claves de API, datos crudos de pacientes, epicrisis reales.

### 0.3 Alcance de Fase 1

Dado el texto de un caso clínico en español (CodiEsp), predecir los códigos de
diagnóstico CIE-10 (principal y secundarios) mediante recuperación sobre el diccionario
oficial CIE-10 + selección por LLM con justificación citando el texto. Evaluado con las
métricas de CodiEsp (precisión, recall, F1 por código y MAP) sobre el set de dev, con
una única corrida final sobre test comparada con el leaderboard del shared task. Incluye
ablations y análisis de errores.

**Fuera de alcance de Fase 1:** procedimientos CIE-9-MC, agrupación GRD, severidad
CC / MCC, alertas de auditoría, capa de detección de PII, demo Streamlit, modelo local,
datos GRD reales de Chile. Todo eso son Fases 2 a 4.

**Criterio de éxito:** un sistema end-to-end funcionando + tabla de resultados +
comparación honesta con la literatura + análisis de errores. No es una meta de F1: el
objetivo es medir y explicar, no alcanzar un número.

### 0.4 Proveedor de LLM y de embeddings, presupuesto

**Proveedor único: OpenAI.**

- Motivo: el modelo no es el cuello de botella de este proyecto (lo es el recall del
  retrieval y el diseño de la evaluación). Cualquier modelo barato actual rinde
  parecido. Se optimiza por fricción, costo y ablations limpios.
- Una sola cuenta, una key, un SDK, salida estructurada estricta (JSON schema nativo),
  mucha documentación. Ideal para un primer proyecto de LLM.
- **LLM workhorse:** `gpt-4o-mini`. **Ablation de calidad:** `gpt-4o`.
- **Embeddings:** `text-embedding-3-small`. **Ablation:** `text-embedding-3-large`.
- Descartado Gemini como principal: los límites de tasa del free tier obligan a meter
  pausas en la evaluación en batch y ensucian las mediciones de latencia.
- Si a futuro se prefiere Anthropic: Haiku 4.5 + embeddings de Voyage, sin cambiar el
  roadmap.

**Embeddings por API (no locales).**

- Motivo: instalar embeddings locales arrastra torch + sentence-transformers + modelo,
  2 a 4 GB de disco, sin ganancia de calidad. El disco de la Mac es una restricción real.
- Desventaja asumida: reproducibilidad. Se mitiga versionando el índice ya calculado en
  el repo (~20 mil vectores en float16 y dimensión reducida, ~30 a 60 MB) y fijando el
  nombre y versión del modelo de embeddings en el README.

**Presupuesto:** tope USD 25 a 30 para todo el proyecto (ablations incluidos). Gasto real
esperado USD 5 a 15. Claves en `.env`, nunca al repo. Límite de gasto mensual en OpenAI
fijado en USD 20 con corte estricto, más alertas al 80% y 100%.

### 0.3 (ajuste tras Bloque A) Alcance de Fase 1

CodiEsp-D es una tarea **multietiqueta a nivel de caso**: el gold lista todos los
códigos de diagnóstico del caso (media ~11 por caso), **sin distinguir principal de
secundarios**. Por lo tanto:

- La evaluación de Fase 1 es predicción del *conjunto* de códigos CIE-10 de diagnóstico
  del caso. Métrica oficial de CodiEsp-D: **MAP** (mean average precision); se reportan
  además precisión, recall y F1 a nivel de código (micro).
- La distinción principal / secundario que hará el LLM es útil para el producto y el
  análisis GRD, pero **no se puede evaluar contra CodiEsp**. No es criterio de éxito de
  Fase 1.

### 0.4 (ajuste tras Bloque A) Base de conocimiento

El `CIE-10.xlsx` de proyecto5 es la versión **OMS 2013** (códigos de 3-4 caracteres).
CodiEsp usa **CIE-10-ES 2018** (ICD-10-CM para diagnósticos, ICD-10-PCS para
procedimientos). No son compatibles. La base de conocimiento del proyecto es la
**lista oficial de códigos válidos de CodiEsp** (Zenodo 3706838, CC-BY 4.0):

- `codiesp-D_codes.tsv`: 98.288 diagnósticos, `codigo <TAB> desc_es <TAB> desc_en`.
- `codiesp-P_codes.tsv`: 87.170 procedimientos.
- Cobertura verificada: el 100% de los códigos gold de train/dev/test está en esta lista.

El `CIE-10.xlsx` OMS se conserva en `data/` solo como referencia, no se usa **en Fase 1**.

### Divergencia España / Chile en los sistemas de codificación (relevante para Fases 2-3)

| | CodiEsp / España | Chile (CMBD / GRD) |
|---|---|---|
| Diagnósticos | CIE-10-ES (≈ ICD-10-CM), 5-7 caracteres | CIE-10 OMS 2013, 3-4 caracteres |
| Procedimientos | ICD-10-PCS, 7 caracteres alfanuméricos | CIE-9-MC v32 (2014), numéricos `xx.xx` |

- Fase 1 (pública) usa CIE-10-ES, sin cambios.
- El lado chileno (privado) reusa la MISMA arquitectura cambiando solo el diccionario
  indexado y el prompt: diagnósticos con el `CIE-10.xlsx` OMS (que SÍ es el correcto
  para Chile), procedimientos con una tabla CIE-9-MC en español (pendiente de conseguir).

### Insumo de Fase 2-3: base CMBD chilena

CMBD (Conjunto Mínimo Básico de Datos) del sistema GRD, egresos codificados de todos los
hospitales públicos de Chile 2019-2025. Diagnóstico principal + secundarios en CIE-10 OMS,
procedimientos en CIE-9-MC. Pública, poco explotada.

- Si incluye la glosa de texto libre del codificador: pares (texto, código) reales =
  set de evaluación "plata" para la aplicación chilena (Fase 2).
- Si son solo códigos: co-ocurrencia para reglas de auditoría (CC/MCC, coherencia dx-px),
  tasas base para IR-GRD, priors de frecuencia.
- No entra en Fase 1: rompería la comparabilidad con el leaderboard de CodiEsp.
- Pendiente: confirmar si el CMBD trae glosa o solo códigos.

### Bloque B: recuperación y diseño revisado del codificador

**Hallazgos** (detalle en `resultados/eval_retrieval_dev.md`):

- Consulta por documento completo: inútil (recall@200 ≈ 0,11). Un caso tiene ~11
  diagnósticos y un embedding no los cubre.
- Consulta por frases + híbrido denso/BM25: recall@200 ≈ 0,31; unión sin recorte 0,52.
- Ese 0,52 es el **techo de la recuperación** sobre descripciones. El 65% del gold no
  recuperado son códigos vagos ("no especificado", "NEOM", "otros..."), sin anclaje
  textual. Ajustar `k_frase` o expandir abreviaturas no lo mueve.

**Decisión de diseño para Bloque C:**

- La recuperación NO es una lista cerrada. Aporta candidatos como pistas (frase-híbrido,
  top ~150) para los diagnósticos específicos.
- El LLM puede **proponer códigos fuera de las pistas** con su propio conocimiento de
  CIE-10 (ahí están los códigos vagos que la recuperación no alcanza).
- Todo código emitido se **valida contra los 98.288 códigos válidos**; los inventados
  se descartan y cuentan como tasa de alucinación.
- Ablation obligatorio: *LLM solo* vs *LLM + candidatos*.

Config de recuperación fijada: `frase-hibrido`, `k_frase=30`, RRF, tope 150 candidatos.
Segmentación por frases y expansión de abreviaturas en `src/recuperar.py`.

### 0.5 Entorno

- Python 3.14.6, `venv` local en `.venv/`.
- **Sin `faiss-cpu`.** No tiene wheel para Python 3.14 y compilar desde fuente falla sin
  `swig`. A la escala de este proyecto (~15 a 20 mil vectores del diccionario CIE-10) la
  búsqueda densa por fuerza bruta con `numpy` es instantánea. faiss solo aporta con
  millones de vectores. La búsqueda vectorial se implementa con `numpy` + `scikit-learn`.
- Clave de OpenAI validada: autentica (HTTP 200) y `gpt-4o-mini` +
  `text-embedding-3-small` disponibles en la cuenta.
