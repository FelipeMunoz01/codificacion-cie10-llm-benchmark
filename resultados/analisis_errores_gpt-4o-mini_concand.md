# Análisis de errores - gpt-4o-mini_concand (dev, 250 casos)

2677 códigos gold, 3588 predichos.

## Destino de cada código GOLD

| categoría | n | % |
|---|---|---|
| acierto exacto | 427 | 16.0% |
| categoría correcta, especificidad equivocada | 522 | 19.5% |
| fallo: estaba en los candidatos, el LLM no lo eligió | 152 | 5.7% |
| fallo: código vago sin anclaje textual | 993 | 37.1% |
| fallo: otro (no recuperado, no vago) | 583 | 21.8% |

## Destino de cada código PREDICHO

| categoría | n | % |
|---|---|---|
| correcto (exacto) | 427 | 11.9% |
| categoría correcta, especificidad equivocada | 682 | 19.0% |
| sobrecodificación (ni exacto ni categoría) | 2479 | 69.1% |

## Ejemplos de gold no acertado

- `q62.11` Oclusión congénita de la unión pieloureteral (estaba en candidatos) — S0004-06142005000900016-1
- `n28.0` Isquemia e infarto del riñón (no recuperado) — S0004-06142005000900016-1
- `n20.0` Cálculo del riñón (no recuperado) — S0004-06142005000900016-1
- `n02.1` Hematuria recidivante y persistente con lesiones glomer (no recuperado) — S0004-06142005001000011-1
- `n21.0` Cálculo en vejiga (no recuperado) — S0004-06142005001000011-1
- `r89.7` Resultados histológicos anormales en muestras de otros  (no recuperado) — S0004-06142005001000011-1
- `n02.8` Hematuria recidivante y persistente con otros cambios m (no recuperado) — S0004-06142005001000011-1
- `t86.11` Rechazo de trasplante renal (estaba en candidatos) — S0004-06142005001000011-1
- `z53.29` Procedimiento y tratamiento no realizados debido a deci (no recuperado) — S0004-06142005001000011-1
- `f12.10` Abuso de cannabis, sin complicaciones (no recuperado) — S0004-06142006000200011-1
- `r50.9` Fiebre, no especificada (estaba en candidatos) — S0004-06142006000200011-1
- `q53.20` Testículo no descendido, bilateral no especificado (estaba en candidatos) — S0004-06142006000500002-3

## Ejemplos de sobrecodificación

- `r93.421` Resultados radiológicos anormales en diagnóstico por im — S0004-06142005000900016-1
- `r93.42` Resultados radiológicos anormales en diagnóstico por im — S0004-06142005000900016-1
- `z42` Contacto para cirugía plástica y reconstructiva después — S0004-06142005000900016-1
- `z87.440` Historia personal de infecciones del tracto urinario — S0004-06142005000900016-1
- `z84.1` Historia familiar de trastornos del riñón y del uréter — S0004-06142005000900016-1
- `r33` Retención urinaria — S0004-06142005000900016-1
- `r53.2` Tetraplejia funcional — S0004-06142005000900016-1
- `r94.4` Resultados anormales en estudios funcionales del riñón — S0004-06142005000900016-1
- `n17.0` Fallo renal agudo con necrosis tubular — S0004-06142005000900016-1
- `n20.0` Cálculo del riñón — S0004-06142005001000011-1
- `z79` Tratamiento farmacológico prolongado (actual) — S0004-06142005001000011-1
- `r94.1` Resultados anormales de estudios funcionales del sistem — S0004-06142005001000011-1
