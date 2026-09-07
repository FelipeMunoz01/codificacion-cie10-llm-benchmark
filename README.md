# Asistente de codificación clínica CIE-10 con recuperación + LLM, evaluado

> Versión didáctica sobre datos públicos (CodiEsp). El motor de reglas de auditoría
> completo y la lógica IR-GRD de Chile viven en un repositorio privado.

Sistema que, dado el texto de un caso clínico en español, propone los códigos de
diagnóstico CIE-10 (principal y secundarios) mediante recuperación sobre el diccionario
oficial CIE-10 y selección por un modelo de lenguaje, con justificación citando el texto.
El foco del proyecto no es "chatear con documentos", sino **construir el sistema y medir
qué tan bien codifica** contra un benchmark público, con análisis de errores y ablations.

## Objetivo y alcance

_(Fase 1, ver `DECISIONES.md` para el alcance cerrado.)_

- Entrada: texto de un caso clínico en español (corpus CodiEsp).
- Salida: códigos CIE-10 de diagnóstico, principal y secundarios, con justificación.
- Evaluación: métricas de CodiEsp (precisión, recall, F1 por código, MAP) sobre dev,
  una única corrida final sobre test, comparada con el leaderboard del shared task.

Fuera de alcance de Fase 1: procedimientos CIE-9-MC, agrupación GRD, severidad CC/MCC,
alertas de auditoría, detección de datos sensibles, despliegue.

## Metodología

_(Pendiente. Se completa a medida que avanza la Fase 1.)_

1. Datos: carga y exploración de CodiEsp y del diccionario CIE-10.
2. Base de conocimiento e índice: normalización del diccionario, embeddings, índice
   vectorial local, búsqueda densa + BM25.
3. Codificador: recuperación de candidatos + selección por LLM con salida estructurada.
4. Evaluación: métricas CodiEsp, ablations, análisis de errores.

## Resultados

_(Pendiente. Tabla de resultados y comparación con la literatura.)_

## Limitaciones

_(Pendiente.)_

## Herramientas

Python, pandas, OpenAI API (LLM y embeddings), faiss-cpu, rank-bm25, scikit-learn,
pydantic.

## Cómo reproducir

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # y completar OPENAI_API_KEY
```

_(Los comandos de cada etapa se agregan a medida que existen los scripts.)_

## Fuentes de datos

- **CodiEsp** (Clinical Case Coding in Spanish, CLEF eHealth 2020), Barcelona
  Supercomputing Center. Casos clínicos en español anotados con CIE-10 y CIE-9-MC.
  Publicado en Zenodo.
- **Diccionario CIE-10** oficial en español (MINSAL Chile / OMS).
