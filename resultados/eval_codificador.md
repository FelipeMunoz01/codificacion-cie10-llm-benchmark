# Codificador LLM sobre CodiEsp-D (dev)

Exacto = código idéntico. cat3 = coincide la categoría de 3 caracteres.

| config | n | MAP | F1_micro | P | R | MAP_cat3 | F1_cat3 | R_cat3 | cods_pred/caso | alucinac/caso | costo_1000casos_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-4o-mini con-cand | 40 | 0.127 | 0.165 | 0.153 | 0.209 |  |  |  | 13.8 | 0.07 | 0.78 |
| gpt-4o-mini_concand | 40 | 0.124 | 0.159 | 0.149 | 0.203 | 0.313 | 0.323 | 0.407 | 13.9 | 0.03 | 0.79 |
| gpt-4o_concand | 30 | 0.23 | 0.305 | 0.344 | 0.318 | 0.413 | 0.476 | 0.486 | 8.0 | 0.03 | 11.34 |
