"""Bloque C: codificador LLM.

Dado el texto de un caso clínico (y opcionalmente una lista de códigos candidatos de
la recuperación), pide a un LLM la lista de códigos de diagnóstico CIE-10-ES del caso.
La salida se valida contra los 98.288 códigos válidos; los que no existen se descartan
y se cuentan como alucinaciones.

    from codificador import Codificador
    cod = Codificador(modelo="gpt-4o-mini")
    r = cod.codificar(texto_caso, candidatos=[...])   # -> ResultadoCodificacion
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from datos import cargar_diccionario

RAIZ = Path(__file__).resolve().parent.parent

SISTEMA = """\
Eres un codificador clínico experto en CIE-10-ES, la versión española de la ICD-10-CM \
usada para codificar diagnósticos en altas hospitalarias.

Tarea: dado un caso clínico, enumera los códigos de diagnóstico CIE-10-ES que un \
codificador profesional asignaría al episodio, ordenados del más central al más \
accesorio. Incluye el diagnóstico principal y TODOS los secundarios.

Los codificadores de estos casos son muy exhaustivos. Codifica también:
- cada signo o síntoma con relevancia clínica aunque no tenga diagnóstico asociado \
(dolor, fiebre, edema, astenia, adenopatía, hematuria, disnea...): capítulo R.
- consumo de tabaco, alcohol u otras drogas siempre que se mencione.
- hallazgos de laboratorio o imagen con significado (anemia, hiperlipidemia, \
microhematuria, masa, derrame...).
- antecedentes personales y familiares que influyen en el manejo (capítulo Z), \
estados posquirúrgicos y dispositivos.
- cuando un órgano o sistema está afectado sin diagnóstico específico, el código \
"trastorno no especificado" de ese órgano.
Un caso típico lleva entre 8 y 15 códigos. Es mejor incluir un código plausible de \
más que omitir uno.

Reglas:
- Solo códigos válidos de CIE-10-ES (formato "N39.0", "R52", "I10").
- Los códigos candidatos son una ayuda de la búsqueda, NO son exhaustivos ni todos \
correctos: añade los que falten con tu conocimiento y descarta los que no correspondan.
- Elige siempre el código más específico que el texto sustente.
- Para cada código, una cita textual breve del caso como evidencia.
- No inventes códigos.

Devuelve JSON: {"codigos": [{"codigo": "N39.0", "evidencia": "cita"}, ...]}"""

# Casos de train usados como ejemplos few-shot (elegidos por diversidad de aparato).
FEW_SHOT_IDS = ["S0004-06142005000700014-1", "S1130-01082007000200008-1"]

_ESQUEMA = {
    "name": "codificacion",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "codigos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "codigo": {"type": "string"},
                        "evidencia": {"type": "string"},
                    },
                    "required": ["codigo", "evidencia"],
                },
            }
        },
        "required": ["codigos"],
    },
}


def normalizar_codigo(c: str) -> str:
    return re.sub(r"\s+", "", str(c)).lower()


@dataclass
class ResultadoCodificacion:
    codigos: list[str]                       # válidos, normalizados, en orden del LLM
    evidencias: dict[str, str]
    alucinados: list[str] = field(default_factory=list)   # emitidos pero no válidos
    corregidos: dict[str, str] = field(default_factory=dict)  # sin punto -> con punto
    uso: dict = field(default_factory=dict)  # tokens


class Codificador:
    def __init__(
        self,
        modelo: str = "gpt-4o-mini",
        temperatura: float = 0.0,
        few_shot: bool = False,
    ) -> None:
        load_dotenv(RAIZ / ".env")
        from openai import OpenAI

        self.cliente = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.modelo = modelo
        self.temperatura = temperatura
        dicc = cargar_diccionario("D")
        self._validos = set(dicc["codigo"])
        self._desc = dict(zip(dicc["codigo"], dicc["desc_es"]))
        # índice sin punto para recuperar códigos que el LLM escribe pegados
        self._sin_punto = {}
        for c in self._validos:
            self._sin_punto.setdefault(c.replace(".", ""), c)
        self._few_shot_msgs = self._construir_few_shot() if few_shot else []

    def _construir_few_shot(self) -> list[dict]:
        from datos import cargar_casos, cargar_gold

        casos = cargar_casos("train").set_index("id")["texto"].to_dict()
        gold = cargar_gold("train", "D")
        msgs = []
        for cid in FEW_SHOT_IDS:
            if cid not in casos:
                continue
            cods = list(dict.fromkeys(gold.loc[gold["id"] == cid, "codigo"]))
            ejemplo = {
                "codigos": [
                    {"codigo": c.upper(), "evidencia": self._desc.get(c, "")[:60]}
                    for c in cods
                ]
            }
            msgs.append({"role": "user", "content": f"CASO CLÍNICO:\n{casos[cid].strip()}"})
            msgs.append({"role": "assistant", "content": json.dumps(ejemplo, ensure_ascii=False)})
        return msgs

    def _resolver(self, bruto: str) -> tuple[str | None, bool]:
        """Devuelve (codigo_valido | None, fue_corregido)."""
        c = normalizar_codigo(bruto)
        if c in self._validos:
            return c, False
        sp = c.replace(".", "")
        if sp in self._sin_punto:
            return self._sin_punto[sp], True
        return None, False

    def _bloque_candidatos(self, candidatos: list[str]) -> str:
        lineas = []
        for c in candidatos:
            c = normalizar_codigo(c)
            d = self._desc.get(c, "")
            lineas.append(f"{c.upper()}: {d}" if d else c.upper())
        return "\n".join(lineas)

    def codificar(
        self, texto_caso: str, candidatos: list[str] | None = None
    ) -> ResultadoCodificacion:
        partes = [f"CASO CLÍNICO:\n{texto_caso.strip()}"]
        if candidatos:
            partes.append(
                "CÓDIGOS CANDIDATOS (ayuda de búsqueda, no exhaustivos):\n"
                + self._bloque_candidatos(candidatos)
            )
        from openai import RateLimitError

        mensajes = [
            {"role": "system", "content": SISTEMA},
            *self._few_shot_msgs,
            {"role": "user", "content": "\n\n".join(partes)},
        ]
        for intento in range(6):
            try:
                resp = self.cliente.chat.completions.create(
                    model=self.modelo,
                    temperature=self.temperatura,
                    messages=mensajes,
                    response_format={"type": "json_schema", "json_schema": _ESQUEMA},
                )
                break
            except RateLimitError:
                time.sleep(2 ** intento + 2)
        else:
            raise RuntimeError("rate limit persistente")
        datos = json.loads(resp.choices[0].message.content)

        codigos: list[str] = []
        evidencias: dict[str, str] = {}
        alucinados: list[str] = []
        corregidos: dict[str, str] = {}
        for item in datos.get("codigos", []):
            bruto = item.get("codigo", "")
            valido, fue_corr = self._resolver(bruto)
            if valido is None:
                alucinados.append(normalizar_codigo(bruto))
                continue
            if fue_corr:
                corregidos[normalizar_codigo(bruto)] = valido
            if valido not in evidencias:
                codigos.append(valido)
                evidencias[valido] = item.get("evidencia", "")
        u = resp.usage
        return ResultadoCodificacion(
            codigos=codigos,
            evidencias=evidencias,
            alucinados=alucinados,
            corregidos=corregidos,
            uso={
                "prompt": u.prompt_tokens,
                "completion": u.completion_tokens,
            },
        )
