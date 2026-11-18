"""Carga y valida acciones.json ANTES de ejecutar ninguna acción."""

import json
import re
from pathlib import Path
from typing import Any

from tareas.errores import AccionNoValida, ConfigError

# Campos admitidos en cada acción y en el filtro; cualquier otro es un error.
CAMPOS_ACCION = {
    "nombre",
    "descripcion",
    "tipo",
    "origen",
    "filtro",
    "destino",
    "plantilla",
    "confirmar",
}
CAMPOS_FILTRO = {"extensiones", "patron", "mas_antiguo_que_dias", "mayor_que_mb"}

TIPOS_VALIDOS = {"mover", "copiar", "renombrar", "borrar"}
TIPOS_CON_DESTINO = {"mover", "copiar"}

# nombre: minúsculas, dígitos y guiones que separen palabras.
_NOMBRE_VALIDO = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
# Huecos admitidos en la plantilla: {fecha:formato}, {n:dígitos}, {ext} y {nombre}.
_HUECO_VALIDO = re.compile(r"\{(?:fecha:[^{}]+|n:\d+|ext|nombre)\}")


def cargar(ruta: Path) -> list[dict]:
    """Lee el fichero de configuración y devuelve la lista de acciones validadas.

    Lanza ConfigError (fichero o raíz) o AccionNoValida (campo de una acción)
    en cuanto encuentra el primer fallo.
    """
    ruta = Path(ruta)
    try:
        texto = ruta.read_text(encoding="utf-8")
    except OSError:
        raise ConfigError(ruta, "no existe o no se puede leer") from None

    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as error:
        motivo = f"no es JSON válido (línea {error.lineno}, columna {error.colno}): {error.msg}"
        raise ConfigError(ruta, motivo) from None

    if not isinstance(datos, dict):
        raise ConfigError(ruta, "la raíz debe ser un objeto con «version» y «acciones»")

    version = datos.get("version")
    if not isinstance(version, int) or isinstance(version, bool):
        raise ConfigError(ruta, "falta «version» o no es un número")
    if version != 1:
        raise ConfigError(ruta, f"«version» debe ser 1, no {version}")

    acciones = datos.get("acciones")
    if not isinstance(acciones, list):
        raise ConfigError(ruta, "falta «acciones» o no es una lista")
    if not acciones:
        raise ConfigError(ruta, "la lista «acciones» no puede estar vacía")

    validadas: list[dict] = []
    nombres: set[str] = set()
    for indice, accion in enumerate(acciones):
        validadas.append(_validar_accion(indice, accion, nombres))
    return validadas


def _validar_accion(indice: int, accion: Any, nombres: set[str]) -> dict:
    """Valida una acción y la devuelve; lanza AccionNoValida si algún campo falla."""
    etiqueta = f"#{indice + 1}"
    if not isinstance(accion, dict):
        raise AccionNoValida(etiqueta, "acción", "debe ser un objeto")
    nombre = accion.get("nombre")
    if isinstance(nombre, str) and nombre:
        etiqueta = nombre

    desconocidos = sorted(accion.keys() - CAMPOS_ACCION)
    if desconocidos:
        campo = desconocidos[0]
        raise AccionNoValida(
            etiqueta,
            campo,
            "no es un campo conocido; los válidos son: "
            + ", ".join(sorted(CAMPOS_ACCION)),
        )

    nombre = _validar_nombre(nombre, etiqueta, nombres)
    _validar_descripcion(nombre, accion.get("descripcion"))
    tipo = _validar_tipo(nombre, accion.get("tipo"))
    _validar_origen(nombre, accion.get("origen"))
    _validar_destino(nombre, tipo, accion.get("destino"))
    _validar_plantilla(nombre, tipo, accion.get("plantilla"))
    _validar_confirmar(nombre, accion.get("confirmar"))
    _validar_filtro(nombre, accion.get("filtro"))

    return dict(accion)


def _validar_nombre(nombre: Any, etiqueta: str, nombres: set[str]) -> str:
    """El nombre es obligatorio, único y va en minúsculas separadas por guiones."""
    if not isinstance(nombre, str) or not nombre:
        raise AccionNoValida(etiqueta, "nombre", "falta o no es una cadena con texto")
    if not _NOMBRE_VALIDO.fullmatch(nombre):
        raise AccionNoValida(
            nombre,
            "nombre",
            "debe ir en minúsculas, con guiones para separar (p. ej. «apartar-copias»)",
        )
    if nombre in nombres:
        raise AccionNoValida(nombre, "nombre", "está repetido; los nombres deben ser únicos")
    nombres.add(nombre)
    return nombre


def _validar_descripcion(nombre: str, descripcion: Any) -> None:
    if not isinstance(descripcion, str) or not descripcion.strip():
        raise AccionNoValida(nombre, "descripcion", "falta o está vacía")


def _validar_tipo(nombre: str, tipo: Any) -> str:
    if not isinstance(tipo, str) or tipo not in TIPOS_VALIDOS:
        raise AccionNoValida(
            nombre,
            "tipo",
            "debe ser uno de: " + ", ".join(sorted(TIPOS_VALIDOS)),
        )
    return tipo


def _validar_origen(nombre: str, origen: Any) -> None:
    if origen is not None and (not isinstance(origen, str) or not origen):
        raise AccionNoValida(nombre, "origen", "debe ser una cadena con texto")


def _validar_destino(nombre: str, tipo: str, destino: Any) -> None:
    if tipo in TIPOS_CON_DESTINO:
        if not isinstance(destino, str) or not destino:
            raise AccionNoValida(
                nombre,
                "destino",
                f"es obligatorio para el tipo «{tipo}»",
            )
        ruta_destino = Path(destino)
        # En Windows «/imagenes» o «C:imagenes» no son absolutos según
        # is_absolute(), pero al unirlos escapan de la carpeta procesada;
        # un ancla no vacía (letra de unidad, / o \ inicial) delata eso.
        if ruta_destino.anchor or ".." in ruta_destino.parts:
            raise AccionNoValida(
                nombre,
                "destino",
                "debe ser relativo a la carpeta que se procesa, sin «..», "
                "sin letra de unidad y sin empezar por / o \\",
            )
    elif destino is not None:
        raise AccionNoValida(
            nombre,
            "destino",
            f"no se usa con el tipo «{tipo}»; solo con mover y copiar",
        )


def _validar_plantilla(nombre: str, tipo: str, plantilla: Any) -> None:
    if tipo != "renombrar":
        if plantilla is not None:
            raise AccionNoValida(
                nombre,
                "plantilla",
                f"no se usa con el tipo «{tipo}»; solo con renombrar",
            )
        return
    if not isinstance(plantilla, str) or not plantilla:
        raise AccionNoValida(nombre, "plantilla", "es obligatoria para el tipo «renombrar»")
    # Revisamos la cadena completa (incluidos los formatos dentro de los
    # huecos): un separador o «..» sacaría el nombre de la carpeta procesada.
    if "/" in plantilla or "\\" in plantilla or ".." in plantilla:
        raise AccionNoValida(
            nombre,
            "plantilla",
            "no puede contener /, \\ ni «..»: el nuevo nombre debe quedarse "
            "dentro de la carpeta que se procesa",
        )
    restante = _HUECO_VALIDO.sub("", plantilla)
    if "{" in restante or "}" in restante:
        raise AccionNoValida(
            nombre,
            "plantilla",
            "solo admite los huecos {fecha:formato}, {n:dígitos}, {ext} y {nombre}",
        )


def _validar_confirmar(nombre: str, confirmar: Any) -> None:
    if confirmar is not None and not isinstance(confirmar, bool):
        raise AccionNoValida(nombre, "confirmar", "debe ser true o false")


def _validar_filtro(nombre: str, filtro: Any) -> None:
    if filtro is None:
        return
    if not isinstance(filtro, dict):
        raise AccionNoValida(nombre, "filtro", "debe ser un objeto")

    desconocidos = sorted(filtro.keys() - CAMPOS_FILTRO)
    if desconocidos:
        campo = desconocidos[0]
        raise AccionNoValida(
            nombre,
            "filtro",
            "el campo «" + campo + "» no es conocido; los válidos son: "
            + ", ".join(sorted(CAMPOS_FILTRO)),
        )

    extensiones = filtro.get("extensiones")
    if extensiones is not None:
        correcta = isinstance(extensiones, list) and extensiones and all(
            isinstance(ext, str)
            and ext.startswith(".")
            and ext == ext.lower()
            for ext in extensiones
        )
        if not correcta:
            raise AccionNoValida(
                nombre,
                "filtro",
                "el campo «extensiones» debe ser una lista de extensiones "
                "en minúsculas y con punto (p. ej. «.jpg»)",
            )

    _validar_patron(nombre, filtro.get("patron"))
    _validar_numero(nombre, filtro, "mas_antiguo_que_dias", "días")
    _validar_numero(nombre, filtro, "mayor_que_mb", "MB")


def _validar_patron(nombre: str, patron: Any) -> None:
    if patron is None:
        return
    if not isinstance(patron, str) or not patron:
        raise AccionNoValida(nombre, "filtro", "el campo «patron» debe ser una cadena con texto")
    try:
        re.compile(patron)
    except re.error as error:
        raise AccionNoValida(
            nombre,
            "filtro",
            f"el campo «patron» no es una expresión regular válida ({error.msg})",
        ) from None


def _validar_numero(nombre: str, filtro: dict, campo: str, unidad: str) -> None:
    valor = filtro.get(campo)
    if valor is None:
        return
    correcto = not isinstance(valor, bool) and isinstance(valor, (int, float)) and valor >= 0
    if not correcto:
        raise AccionNoValida(
            nombre,
            "filtro",
            f"el campo «{campo}» debe ser un número de {unidad} mayor o igual que 0",
        )
