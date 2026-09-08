"""Capa de reglas deterministas sobre la salida del codificador.

En esta versión pública la capa es una interfaz con dos reglas de ejemplo. El conjunto
completo de reglas de auditoría (agrupación IR-GRD, severidad CC/MCC, anti-fragmentación
de procedimientos, vía de acceso inherente, etc.) es parte del sistema de producción y
vive en un repositorio privado.

La idea: el LLM propone códigos; estas funciones, sin IA, corrigen o marcan la salida
según normas de codificación. Se aplican en orden con `aplicar_reglas`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Aviso:
    codigo: str
    regla: str
    mensaje: str


Regla = "Callable[[list[str]], tuple[list[str], list[Aviso]]]"


def quitar_duplicados_de_categoria(codigos: list[str]) -> tuple[list[str], list[Aviso]]:
    """Ejemplo: si hay dos códigos de la misma categoría de 3 caracteres y uno es el
    genérico "no especificado", se marca como posible redundancia (no se elimina).
    """
    avisos: list[Aviso] = []
    por_cat: dict[str, list[str]] = {}
    for c in codigos:
        por_cat.setdefault(c.replace(".", "")[:3], []).append(c)
    for cat, cs in por_cat.items():
        if len(cs) > 1:
            avisos.append(Aviso(", ".join(cs), "duplicado_categoria",
                                f"varios códigos en la categoría {cat.upper()}; revisar"))
    return codigos, avisos


def marcar_codigos_dudosos_sin_evidencia(codigos: list[str],
                                         evidencias: dict[str, str] | None = None
                                         ) -> tuple[list[str], list[Aviso]]:
    """Ejemplo: marca los códigos cuya evidencia textual está vacía o es muy corta."""
    avisos: list[Aviso] = []
    evidencias = evidencias or {}
    for c in codigos:
        if len(evidencias.get(c, "").strip()) < 8:
            avisos.append(Aviso(c, "sin_evidencia", "el LLM no citó evidencia clara"))
    return codigos, avisos


def aplicar_reglas(codigos: list[str], evidencias: dict[str, str] | None = None
                   ) -> tuple[list[str], list[Aviso]]:
    """Aplica las reglas disponibles y acumula los avisos.

    NOTA: implementación de ejemplo. La versión de producción encadena ~30 reglas.
    """
    avisos: list[Aviso] = []
    codigos, a = quitar_duplicados_de_categoria(codigos)
    avisos += a
    codigos, a = marcar_codigos_dudosos_sin_evidencia(codigos, evidencias)
    avisos += a
    return codigos, avisos
