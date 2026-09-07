# Recuperación pura - recall@k (split dev)

Embeddings: text-embedding-3-small dim 512. 250 casos, 15.6 frases/caso, 10.7 códigos/caso.

recall@k = fracción de códigos gold del caso presentes entre los k candidatos, promediada sobre casos.

| estrategia | r@20 | r@50 | r@100 | r@150 | r@200 | r@300 | r@500 |
|---|---|---|---|---|---|---|---|
| doc-denso | 0.043 | 0.060 | 0.082 | 0.100 | 0.108 | 0.124 | 0.161 |
| frase-denso (kf=30) | 0.049 | 0.098 | 0.160 | 0.188 | 0.212 | 0.242 | 0.264 |
| frase-hibrido (kf=30) | 0.093 | 0.156 | 0.224 | 0.268 | 0.307 | 0.354 | 0.405 |
| frase-denso (kf=50) | 0.043 | 0.080 | 0.133 | 0.174 | 0.207 | 0.243 | 0.292 |
| frase-hibrido (kf=50) | 0.082 | 0.140 | 0.202 | 0.251 | 0.284 | 0.337 | 0.403 |
| TECHO union (kf=50, sin cap) | 0.516 | 0.516 | 0.516 | 0.516 | 0.516 | 0.516 | 0.516 |

## Análisis

- **La consulta por documento completo fracasa** (recall@200 = 0.11). Un caso tiene
  ~11 diagnósticos distintos y un solo embedding no los representa.
- **Consulta por frases + híbrido (denso + BM25)** sube a recall@200 = 0.31, y la
  unión sin recortar llega a **0.52**. Ese 0.52 es el techo de la recuperación sobre
  descripciones.
- **La expansión de abreviaturas y subir `k_frase` no mueven la aguja.** El cuello de
  botella no es el ajuste fino.
- **Por qué el techo es 0.52:** de los códigos gold que la recuperación NO encuentra,
  el **65%** son códigos vagos ("no especificado", "NEOM", "otros trastornos
  especificados de..."). No tienen anclaje textual: no se puede recuperar "Enfermedad
  NEOM" por similitud semántica con una epicrisis. CodiEsp-D exige ~11 códigos por
  caso, muchos de ellos administrativos y exhaustivos.

## Consecuencia para el diseño (Bloque C)

La recuperación **no** puede ser una lista cerrada de la que el LLM elige, porque
dejaría fuera de alcance la mitad del gold. Diseño revisado:

1. La recuperación aporta **candidatos como pistas** (frase-hibrido, top ~150) para
   anclar los diagnósticos específicos y nombrables.
2. El LLM ve esas pistas **y puede proponer códigos fuera de la lista** usando su
   propio conocimiento de CIE-10 (es donde están los códigos vagos que la
   recuperación no alcanza).
3. **Todo código emitido se valida contra la lista de 98.288 códigos válidos.** Los
   inventados se descartan y se cuentan como métrica de alucinación.
4. Ablation explícito: *LLM solo* vs *LLM + candidatos recuperados*, para medir cuánto
   aporta la recuperación de verdad.
