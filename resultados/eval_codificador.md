# Codificador LLM sobre CodiEsp (D y P)

MAP es la métrica oficial del shared task. cat3 = coincide la categoría (3 primeros caracteres).
Referencia SOTA supervisado 2020 (CodiEsp-D): MAP 0,593.

| config | n | MAP exacto | MAP cat3 | F1 exacto | cods/caso | gold/caso | aluc/caso | USD/1000 |
|---|---|---|---|---|---|---|---|---|
| gpt-4o-mini_concand | 40 | 0.124 | 0.313 | 0.159 | 13.9 | 12.0 | 0.03 | 0.79 |
| gpt-4o_concand | 30 | 0.23 | 0.413 | 0.305 | 8.0 | 10.8 | 0.03 | 11.34 |
| gpt-4o-mini_sincand | 100 | 0.097 | 0.25 | 0.154 | 12.7 | 12.6 | 0.39 | 0.37 |
| gpt-4o-mini_concand_fewshot | 100 | 0.096 | 0.285 | 0.16 | 10.9 | 12.6 | 0.04 | 0.91 |
| gpt-4o-mini_concand_pmin | 100 | 0.069 | 0.228 | 0.133 | 6.0 | 12.6 | 0.01 | 0.62 |
| P_gpt-4o-mini_concand | 60 | 0.014 | 0.156 | 0.044 | 4.0 | 4.5 | 0.03 | 0.78 |
