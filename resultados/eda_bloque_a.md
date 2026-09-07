# EDA Bloque A - CodiEsp subtrack D (diagnósticos)

## Casos y códigos por split

| split | casos | filas gold | códigos/caso (media) | mediana | min | max |
|---|---|---|---|---|---|---|
| train | 500 | 5639 | 11.3 | 10 | 1 | 40 |
| dev | 250 | 2677 | 10.7 | 10 | 1 | 33 |
| test | 250 | 2842 | 11.4 | 10 | 1 | 35 |

## Longitud de los casos (palabras)

| split | media | p10 | p50 | p90 | max |
|---|---|---|---|---|---|
| train | 349 | 164 | 314 | 576 | 1172 |
| dev | 352 | 173 | 328 | 570 | 956 |
| test | 353 | 161 | 330 | 555 | 965 |

## Diccionario CIE-10-ES (subtrack D)

- Códigos en el diccionario: 98,288

### Cobertura del gold por el diccionario

| split | códigos únicos gold | en diccionario | fuera | cobertura |
|---|---|---|---|---|
| train | 1767 | 1767 | 0 | 100.0% |
| dev | 1158 | 1158 | 0 | 100.0% |
| test | 1143 | 1143 | 0 | 100.0% |

Todos los códigos gold están en el diccionario.

## Códigos de dev/test ya vistos en train

| split | códigos únicos | también en train | solo en este split | vistos |
|---|---|---|---|---|
| dev | 1158 | 731 | 427 | 63.1% |
| test | 1143 | 704 | 439 | 61.6% |

## Especificidad de los códigos gold (nº de caracteres alfanuméricos)

| split | 3 (categoría) | 4 | 5 | 6+ |
|---|---|---|---|---|
| train | 79 | 890 | 520 | 278 |
| dev | 48 | 623 | 323 | 164 |
| test | 55 | 598 | 324 | 166 |

## 15 códigos de diagnóstico más frecuentes en train

| código | casos | descripción |
|---|---|---|
| r52 | 112 | Dolor, no especificado |
| r69 | 99 | Enfermedad NEOM |
| r50.9 | 97 | Fiebre, no especificada |
| i10 | 77 | Hipertensión esencial (primaria) |
| r60.9 | 66 | Edema, no especificado |
| r59.9 | 65 | Adenomegalia, no especificada |
| r53.1 | 57 | Astenia |
| r11.10 | 47 | Vómitos, no especificados |
| r59.0 | 46 | Adenomegalia localizada |
| r10.9 | 46 | Dolor abdominal no especificado |
| r58 | 45 | Hemorragia, no clasificada bajo otro concepto |
| b99.9 | 45 | Enfermedad infecciosa no especificada |
| d64.9 | 43 | Anemia, no especificada |
| e11.9 | 41 | Diabetes mellitus tipo 2 sin complicaciones |
| i96 | 37 | Gangrena, no clasificada bajo otro concepto |
