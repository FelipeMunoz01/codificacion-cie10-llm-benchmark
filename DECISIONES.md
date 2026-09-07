# Decisiones del proyecto

Registro de decisiones tomadas, con su fecha y el motivo. Igual que en proyecto5.

---

## 2026-09-06 · Fase 0

### 0.1 Nombre del repo público

**`asistente-codificacion-clinica-cie10`**

- CodiEsp es dato clínico de España, así que se evita "chile" en el nombre del repo
  público. Lo específico de Chile (IR-GRD, MINSAL) vive en el repo privado.
- Se prefirió el enfoque "asistente / servicio" por sobre atar el nombre al dataset,
  por si más adelante se amplía a otros corpus.

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

### 0.5 Entorno

- Python 3.14.6, `venv` local en `.venv/`.
- **Sin `faiss-cpu`.** No tiene wheel para Python 3.14 y compilar desde fuente falla sin
  `swig`. A la escala de este proyecto (~15 a 20 mil vectores del diccionario CIE-10) la
  búsqueda densa por fuerza bruta con `numpy` es instantánea. faiss solo aporta con
  millones de vectores. La búsqueda vectorial se implementa con `numpy` + `scikit-learn`.
- Clave de OpenAI validada: autentica (HTTP 200) y `gpt-4o-mini` +
  `text-embedding-3-small` disponibles en la cuenta.
