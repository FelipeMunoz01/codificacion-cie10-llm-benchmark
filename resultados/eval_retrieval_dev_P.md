# Recuperación pura - recall@k (split dev, subtrack P)

Embeddings: text-embedding-3-small dim 512. 250 casos, 15.6 frases/caso, 3.7 códigos/caso.

recall@k = fracción de códigos gold del caso presentes entre los k candidatos, promediada sobre casos.

| estrategia | r@20 | r@50 | r@100 | r@150 | r@200 | r@300 | r@500 |
|---|---|---|---|---|---|---|---|
| doc-denso | 0.002 | 0.011 | 0.015 | 0.019 | 0.024 | 0.045 | 0.058 |
| frase-denso (kf=30) | 0.012 | 0.029 | 0.048 | 0.070 | 0.080 | 0.094 | 0.106 |
| frase-hibrido (kf=30) | 0.026 | 0.065 | 0.106 | 0.138 | 0.158 | 0.186 | 0.208 |
| frase-denso (kf=50) | 0.006 | 0.025 | 0.050 | 0.060 | 0.075 | 0.102 | 0.129 |
| frase-hibrido (kf=50) | 0.017 | 0.043 | 0.100 | 0.126 | 0.149 | 0.184 | 0.211 |
| TECHO union (kf=50, sin cap) | 0.270 | 0.270 | 0.270 | 0.270 | 0.270 | 0.270 | 0.270 |
