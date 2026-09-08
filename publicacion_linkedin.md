Llevo 11 años codificando GRD y este año estoy haciendo un diplomado en IA aplicada al
diagnóstico médico. Era cuestión de tiempo que juntara las dos cosas y me hiciera la
pregunta obvia: ¿qué tan cerca está hoy un modelo de lenguaje de hacer, o al menos
asistir, el trabajo de un codificador clínico?

En vez de quedarme con la impresión, lo medí.

Armé un sistema de codificación automática de diagnósticos CIE-10 sobre CodiEsp, el
corpus público de casos clínicos en español que se usó en un shared task en 2020. El
sistema recupera códigos candidatos del catálogo oficial y un modelo de OpenAI elige y
justifica cada uno con una cita del texto. Todo lo que propone el modelo se valida
contra los 98.288 códigos válidos.

El resultado, sin entrenar nada:

→ El mejor sistema de aquel shared task, con entrenamiento supervisado, llegó a MAP
0,593. Este, con gpt-4o-mini, llega a 0,090 en el conjunto de test. Con gpt-4o sube a
0,196, a diecinueve veces el costo por caso.

→ La distancia es real y tiene explicación. El 37% de los códigos que exige el gold son
códigos vagos ("no especificado", "sin otra especificación") que no tienen anclaje en el
texto: no se pueden recuperar por parecido semántico ni adivinar de forma fiable.

→ De los fallos que sí son clínicos, la mitad son de especificidad, no de criterio: el
modelo dice "cálculo urinario" bien, pero elige N20.1 en vez de N20.0. Si se evalúa a
nivel de categoría de 3 caracteres, el acierto casi se duplica.

→ Añadir la recuperación de candidatos casi no mejora la exactitud, pero baja las
invenciones de código de 0,39 a 0,05 por caso. Su valor es anclar el modelo, no hacerlo
acertar más.

→ El prompt importa mucho. Uno escueto hace que el modelo codifique 6 diagnósticos por
caso cuando el promedio real es 13.

La conclusión, para mi trabajo, es tranquilizadora y a la vez interesante: un LLM
genérico no reemplaza a un codificador, y la brecha no es de "más datos" sino
estructural. Pero como apoyo acotado, con validación encima y sobre la parte específica
y nombrable del diagnóstico, la herramienta tiene dónde aportar.

Todo el código, la evaluación y el análisis de errores están en GitHub:
https://github.com/FelipeMunoz01/codificacion-cie10-llm-benchmark
