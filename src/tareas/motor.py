"""Motor: guarda las acciones, selecciona ficheros y ejecuta la elegida.

No imprime nada ni pide confirmación: de eso se encarga cli.py.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

from tareas.errores import TareasError
from tareas.acciones import Accion, Resultado

_SEGUNDOS_DIA = 24 * 60 * 60
_BYTES_MB = 1024 * 1024


class Motor:
    """Construye las acciones del fichero de configuración y las ejecuta."""

    def __init__(self, acciones: list[dict]) -> None:
        # Los nombres ya son únicos porque config.cargar() los ha validado.
        self._acciones: dict[str, Accion] = {
            accion["nombre"]: Accion.desde_config(accion) for accion in acciones
        }

    def obtener(self, nombre: str) -> Accion | None:
        """Devuelve la acción «nombre» o None si no existe, sin ejecutarla.

        Para que quien llama (cli.py) pueda mirar propiedades como
        ``destructiva`` antes de decidir si pide confirmación.
        """
        return self._acciones.get(nombre)

    def seleccionar(self, carpeta: Path, filtro: dict | None = None) -> list[Path]:
        """Ficheros de la carpeta que cumplen el filtro, por nombre (A→Z).

        Solo ficheros sueltos: las carpetas nunca se procesan. Sin filtro,
        selecciona todos.
        """
        carpeta = Path(carpeta)
        if not carpeta.is_dir():
            raise TareasError(f"la carpeta «{carpeta}» no existe o no es una carpeta")

        filtro = filtro or {}
        extensiones = filtro.get("extensiones") or []
        patron = re.compile(filtro["patron"]) if filtro.get("patron") else None
        dias = filtro.get("mas_antiguo_que_dias")
        megas = filtro.get("mayor_que_mb")
        ahora = time.time()

        try:
            entradas = sorted(
                carpeta.iterdir(), key=lambda ruta: ruta.name.casefold()
            )
        except OSError:
            raise TareasError(
                f"no se puede leer el contenido de la carpeta «{carpeta}»"
            ) from None

        seleccionados: list[Path] = []
        for entrada in entradas:
            try:
                if not entrada.is_file():
                    continue
                datos = entrada.stat()
            except OSError:
                continue  # sin permisos o enlace roto: no se puede procesar
            if extensiones and entrada.suffix.lower() not in extensiones:
                continue
            if patron is not None and patron.search(entrada.name) is None:
                continue
            if dias is not None and ahora - datos.st_mtime < dias * _SEGUNDOS_DIA:
                continue
            if megas is not None and datos.st_size <= megas * _BYTES_MB:
                continue
            seleccionados.append(entrada)
        return seleccionados

    def ejecutar(
        self,
        nombre: str,
        carpeta: Path | None = None,
        simular: bool = False,
    ) -> list[Resultado]:
        """Ejecuta la acción «nombre» sobre la carpeta (o sobre su «origen»).

        Devuelve un Resultado por fichero procesado. Si la acción o la
        carpeta no existen, lanza TareasError con mensaje humano.
        """
        accion = self._acciones.get(nombre)
        if accion is None:
            disponibles = ", ".join(sorted(self._acciones))
            raise TareasError(
                f"la acción «{nombre}» no existe; disponibles: {disponibles}"
            )

        # expanduser() para que funcionen rutas con «~», p. ej. ~/pruebas-tareas.
        if carpeta is not None:
            carpeta_resuelta = Path(carpeta).expanduser()
        elif accion.origen is not None:
            # Path() por si origen llega como texto del JSON.
            carpeta_resuelta = Path(accion.origen).expanduser()
        else:
            carpeta_resuelta = Path(".")
        ficheros = self.seleccionar(carpeta_resuelta, accion.filtro)
        return accion.ejecutar(ficheros, simular)
