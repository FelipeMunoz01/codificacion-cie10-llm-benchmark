# Codificador LLM sobre CodiEsp-D

MAP es la métrica oficial del shared task. cat3 = coincide la categoría de 3 caracteres.
Referencia SOTA supervisado 2020: MAP 0,593.

| split | config | n | MAP exacto | MAP cat3 | F1 exacto | P | R | cods/caso | aluc/caso | USD/1000 |
|---|---|---|---|---|---|---|---|---|---|---|
| dev | gpt-4o-mini_concand | 250 | 0.092 | 0.274 | 0.13 | 0.118 | 0.175 | 14.4 | 0.03 | 0.83 |
| test | gpt-4o-mini_concand | 250 | 0.09 | 0.267 | 0.134 | 0.126 | 0.171 | 14.2 | 0.06 | 0.82 |
| dev | gpt-4o-mini_sincand | 100 | 0.097 | 0.25 | 0.154 | 0.158 | 0.164 | 12.7 | 0.39 | 0.37 |
| dev | gpt-4o-mini_concand_fewshot | 100 | 0.096 | 0.285 | 0.16 | 0.174 | 0.165 | 10.9 | 0.04 | 0.91 |
| dev | gpt-4o-mini_concand_pmin | 100 | 0.069 | 0.228 | 0.133 | 0.219 | 0.105 | 6.0 | 0.01 | 0.62 |
| dev | gpt-4o_concand | 50 | 0.196 | 0.366 | 0.281 | 0.322 | 0.281 | 8.5 | 0.04 | 15.77 |
