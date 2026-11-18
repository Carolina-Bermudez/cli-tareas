"""Acciones de tareas: cada tipo sabe procesar un fichero concreto.

Toda escritura en el disco (mkdir, move, copy, rename, unlink) queda SIEMPRE
detrás del ``if not simular``: con ``simular=True`` solo se leen datos
(stat, exists) y se devuelven resultados de estado «simulado».
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import re
import shutil
from pathlib import Path
from typing import Any, ClassVar, Literal

from tareas.errores import TareasError

Estado = Literal["hecho", "simulado", "saltado"]


@dataclass
class Resultado:
    """Lo que devuelve aplicar una acción a un fichero.

    ``destino`` es ``None`` cuando no aplica (borrar) o el fichero se saltó
    por un error antes de calcularlo.
    """

    origen: Path
    destino: Path | None
    estado: Estado


def destino_libre(ruta: Path) -> Path:
    """Devuelve una ruta que no existe, para nunca sobrescribir.

    Añade el sufijo « (1)», « (2)»… antes de la extensión:
    foto.jpg → foto (1).jpg. Sin extensión: informe.pdf → informe (1).pdf
    y nota → nota (1).
    """
    if not ruta.exists():
        return ruta
    numero = 1
    while True:
        candidata = ruta.with_name(f"{ruta.stem} ({numero}){ruta.suffix}")
        if not candidata.exists():
            return candidata
        numero += 1


class Accion(ABC):
    """Acción abstracta: un tipo concreto sabe aplicar un fichero.

    Las subclases se apuntan solas al registro: basta con definir ``TIPO``
    en la propia clase y ``__init_subclass__`` hace el resto.
    """

    TIPO: str = ""
    destructiva: bool = False

    _registro: ClassVar[dict[str, type["Accion"]]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Solo se registra si la propia clase define TIPO (no lo hereda),
        # así una clase base intermedia abstracta no se apunta.
        tipo = cls.__dict__.get("TIPO", "")
        if tipo:
            Accion._registro[tipo] = cls

    def __init__(self, config: dict) -> None:
        self.nombre: str = config["nombre"]
        self.descripcion: str = config["descripcion"]
        # Carpeta por defecto si quien llama no pasa una; puede ser None.
        self.origen: Path | None = (
            Path(config["origen"]) if config.get("origen") else None
        )
        self.filtro: dict = config.get("filtro") or {}

    @classmethod
    def desde_config(cls, config: dict) -> "Accion":
        """Fábrica: crea la subclase del tipo indicado (mover, copiar, …)."""
        tipo = config.get("tipo", "")
        try:
            subclase = cls._registro[tipo]
        except KeyError:
            disponibles = ", ".join(sorted(cls._registro)) or "ninguno"
            raise TareasError(
                f"tipo de acción desconocido: «{tipo}»; válidos: {disponibles}"
            ) from None
        return subclase(config)

    @abstractmethod
    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        """Aplica la acción a un fichero; ``n`` es su posición (para {n:03})."""

    def ejecutar(self, ficheros: list[Path], simular: bool) -> list[Resultado]:
        """Aplica la acción a cada fichero; un error no corta el resto.

        Un fichero que falla (permisos, desaparecido…) sale como «saltado».
        """
        resultados: list[Resultado] = []
        for n, fichero in enumerate(ficheros, start=1):
            try:
                resultados.append(self.aplicar(fichero, n, simular))
            except (OSError, ValueError):
                resultados.append(Resultado(fichero, None, "saltado"))
        return resultados


class _ConDestino(Accion):
    """Común a mover y copiar: destino relativo a la carpeta del fichero."""

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        # Ya validado en config.py: cadena relativa, sin anclas ni «..».
        self.destino = Path(config["destino"])

    def _carpeta_destino(self, fichero: Path) -> Path:
        # El destino es relativo a la carpeta que se procesa, es decir, a la
        # carpeta del fichero (no al directorio actual del programa).
        return fichero.parent / self.destino


class Mover(_ConDestino):
    """Mueve el fichero a CARPETA/destino sin sobrescribir nada."""

    TIPO = "mover"

    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        carpeta_destino = self._carpeta_destino(fichero)
        # destino_libre solo lee el disco (exists), así que también en
        # simulación se calcula: así muestra el mismo destino que se usaría
        # de verdad, con « (1)» si hiciera falta. Sin tocar nada del disco.
        destino_final = destino_libre(carpeta_destino / fichero.name)
        if simular:
            return Resultado(fichero, destino_final, "simulado")
        # mkdir antes de mover: si la carpeta no existe, shutil.move
        # renombraría el fichero a «imagenes» y el siguiente se sobrescribiría.
        carpeta_destino.mkdir(parents=True, exist_ok=True)
        shutil.move(str(fichero), str(destino_final))
        return Resultado(fichero, destino_final, "hecho")


class Copiar(_ConDestino):
    """Copia el fichero a CARPETA/destino sin sobrescribir nada."""

    TIPO = "copiar"

    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        carpeta_destino = self._carpeta_destino(fichero)
        destino_final = destino_libre(carpeta_destino / fichero.name)
        if simular:
            return Resultado(fichero, destino_final, "simulado")
        carpeta_destino.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fichero, destino_final)
        return Resultado(fichero, destino_final, "hecho")


class Renombrar(Accion):
    """Renombra el fichero dentro de su carpeta siguiendo la plantilla."""

    TIPO = "renombrar"

    # Huecos de la plantilla; debe coincidir con _HUECO_VALIDO de config.py.
    _HUECO = re.compile(r"\{(?:fecha:([^{}]+)|n:(\d+)|ext|nombre)\}")

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.plantilla: str = config["plantilla"]

    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        nuevo_nombre = self._rellenar(fichero, n)
        if nuevo_nombre == fichero.name:
            # Renombrar a sí mismo no tiene sentido y « (1)» no lo arregla.
            return Resultado(fichero, fichero, "saltado")
        destino_final = destino_libre(fichero.parent / nuevo_nombre)
        if simular:
            return Resultado(fichero, destino_final, "simulado")
        fichero.rename(destino_final)
        return Resultado(fichero, destino_final, "hecho")

    def _rellenar(self, fichero: Path, n: int) -> str:
        """Sustituye los huecos {fecha:…}, {n:…}, {ext} y {nombre}."""
        extension = fichero.suffix.lower()  # con el punto, p. ej. «.jpg»
        modificado = datetime.fromtimestamp(fichero.stat().st_mtime)

        def sustituye(coincidencia: re.Match[str]) -> str:
            formato_fecha, digitos = coincidencia.group(1), coincidencia.group(2)
            if formato_fecha is not None:
                # Fecha de modificación del fichero, no la actual.
                return modificado.strftime(formato_fecha)
            if digitos is not None:
                return str(n).zfill(int(digitos))
            if coincidencia.group(0) == "{ext}":
                return extension
            return fichero.stem  # {nombre}, sin la extensión

        return self._HUECO.sub(sustituye, self.plantilla)


class Borrar(Accion):
    """Borra el fichero: es la única acción destructiva.

    Pide confirmación quien llama (cli.py), salvo --si.
    """

    TIPO = "borrar"
    destructiva = True

    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        if simular:
            return Resultado(fichero, None, "simulado")
        fichero.unlink()
        return Resultado(fichero, None, "hecho")
