"""Órdenes de la CLI de tareas: version, listar, validar, acciones y ejecutar."""

from datetime import datetime
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from tareas import __version__, config, errores
from tareas.motor import Motor

# En Windows la consola puede arrancar con cp1252, que no puede dibujar el
# «✔» ni las tildes. Se fuerza UTF-8 en la salida si el intérprete lo permite.
for _flujo in (sys.stdout, sys.stderr):
    if hasattr(_flujo, "reconfigure"):
        _flujo.reconfigure(encoding="utf-8")

app = typer.Typer(
    help="Automatiza tareas repetitivas con ficheros desde la terminal.",
    no_args_is_help=True,
    add_completion=False,
)

consola = Console()
consola_errores = Console(stderr=True)


@app.callback()
def principal(
    ctx: typer.Context,
    config_ruta: Annotated[
        Path,
        typer.Option(
            "--config",
            help="Fichero de configuración de acciones. Por defecto, ./acciones.json.",
        ),
    ] = Path("acciones.json"),
) -> None:
    """Opciones generales de tareas."""
    ctx.obj = {"config": config_ruta}


@app.command()
def validar(ctx: typer.Context) -> None:
    """Comprueba que el fichero de configuración de acciones es válido."""
    ruta = ctx.obj["config"]
    try:
        acciones = config.cargar(ruta)
    except errores.TareasError as e:
        consola_errores.print(f"[red]Error:[/red] {escape(e.mensaje)}")
        raise typer.Exit(e.codigo_salida)

    tabla = Table(title=f"Acciones de {escape(str(ruta))}")
    tabla.add_column("Nombre")
    tabla.add_column("Tipo")
    tabla.add_column("Filtro")
    tabla.add_column("Extra")
    for accion in acciones:
        filtro = accion.get("filtro", {})
        filtro_resumen = "sí" if filtro else "—"
        extra_campo = "destino" if "destino" in accion else "plantilla"
        extra = f"{extra_campo}: {accion[extra_campo]}" if extra_campo in accion else "—"
        tabla.add_row(escape(accion["nombre"]), escape(accion["tipo"]), filtro_resumen, escape(extra))

    consola.print(tabla)
    if len(acciones) == 1:
        resumen = "✔ 1 acción válida"
    else:
        resumen = f"✔ {len(acciones)} acciones válidas"
    consola.print(f"[green]{resumen}[/green]")


@app.command("acciones")
def acciones(ctx: typer.Context) -> None:
    """Muestra las acciones definidas en el fichero de configuración."""
    ruta = ctx.obj["config"]
    try:
        lista = config.cargar(ruta)
    except errores.TareasError as e:
        consola_errores.print(f"[red]Error:[/red] {escape(e.mensaje)}")
        raise typer.Exit(e.codigo_salida)

    if not lista:
        consola.print(
            f"[yellow]El fichero [bold]{escape(str(ruta))}[/bold] no define ninguna acción.[/yellow]"
        )
        return

    tabla = Table(title=f"Acciones de {escape(str(ruta))}")
    tabla.add_column("Nombre")
    tabla.add_column("Tipo")
    tabla.add_column("Descripción")
    for accion in lista:
        tabla.add_row(
            escape(accion["nombre"]),
            escape(accion["tipo"]),
            escape(accion["descripcion"]),
        )
    consola.print(tabla)


# Colores del estado de cada resultado, para leer la tabla de un vistazo.
_COLOR_ESTADO = {"hecho": "green", "simulado": "yellow", "saltado": "red"}


@app.command()
def ejecutar(
    ctx: typer.Context,
    nombre: Annotated[
        str,
        typer.Argument(help="Nombre de la acción a ejecutar."),
    ],
    carpeta: Annotated[
        Path | None,
        typer.Argument(
            help="Carpeta sobre la que actuar. Por defecto, el «origen» de la acción o la actual. Acepta rutas con ~.",
        ),
    ] = None,
    simular: Annotated[
        bool,
        typer.Option("--simular", help="Muestra qué haría la acción sin tocar ningún fichero."),
    ] = False,
    si: Annotated[
        bool,
        typer.Option("--si", help="No pide confirmación en las acciones destructivas."),
    ] = False,
) -> None:
    """Ejecuta la acción «nombre» sobre una carpeta de ficheros."""
    ruta = ctx.obj["config"]
    try:
        lista = config.cargar(ruta)
    except errores.TareasError as e:
        consola_errores.print(f"[red]Error:[/red] {escape(e.mensaje)}")
        raise typer.Exit(e.codigo_salida)

    motor = Motor(lista)

    # La confirmación va ANTES de ejecutar nada: si es destructiva y no hay
    # --simular ni --si, se pregunta. El nombre desconocido lo detecta
    # motor.ejecutar() más abajo con su propio mensaje.
    accion = motor.obtener(nombre)
    if accion is not None and accion.destructiva and not simular and not si:
        if not typer.confirm(f"La acción «{nombre}» borra ficheros. ¿Continuar?"):
            consola.print("[yellow]Cancelado: no se ha borrado nada.[/yellow]")
            raise typer.Exit(1)

    try:
        resultados = motor.ejecutar(nombre, carpeta, simular)
    except errores.TareasError as e:
        consola_errores.print(f"[red]Error:[/red] {escape(e.mensaje)}")
        raise typer.Exit(e.codigo_salida)

    if not resultados:
        consola.print(
            "[yellow]Ningún fichero cumple el filtro de la acción; no hay nada que hacer.[/yellow]"
        )
        return

    titulo = f"Acción {escape(nombre)}"
    if simular:
        titulo += " (simulación)"
    tabla = Table(title=titulo)
    tabla.add_column("Fichero")
    tabla.add_column("Destino")
    tabla.add_column("Estado")
    for resultado in resultados:
        destino = escape(str(resultado.destino)) if resultado.destino is not None else "—"
        color = _COLOR_ESTADO.get(resultado.estado)
        estado = f"[{color}]{resultado.estado}[/{color}]" if color else resultado.estado
        tabla.add_row(escape(resultado.origen.name), destino, estado)
    consola.print(tabla)

    hechos = sum(1 for r in resultados if r.estado == "hecho")
    simulados = sum(1 for r in resultados if r.estado == "simulado")
    saltados = sum(1 for r in resultados if r.estado == "saltado")
    consola.print(
        f"[green]✔ {hechos} hechos[/green] · {simulados} simulados · {saltados} saltados"
    )

    if simular:
        consola.print(
            "[yellow]Para hacerlo de verdad, repite la orden sin --simular.[/yellow]"
        )


@app.command()
def version() -> None:
    """Muestra la versión del programa."""
    consola.print(f"tareas {__version__}")


@app.command()
def listar(
    carpeta: Annotated[
        Path,
        typer.Argument(
            help="Carpeta a listar. Por defecto, la actual. Acepta rutas con ~.",
        ),
    ] = Path("."),
) -> None:
    """Lista el contenido de una carpeta: carpetas primero, luego alfabético."""
    ruta = carpeta.expanduser()

    if not ruta.exists():
        consola_errores.print(
            f"[red]Error:[/red] la ruta [bold]{escape(str(ruta))}[/bold] no existe o no se puede acceder."
        )
        raise typer.Exit(1)
    if not ruta.is_dir():
        consola_errores.print(
            f"[red]Error:[/red] [bold]{escape(str(ruta))}[/bold] no es una carpeta."
        )
        raise typer.Exit(1)

    try:
        entradas = list(ruta.iterdir())
    except OSError:
        consola_errores.print(
            f"[red]Error:[/red] no se puede leer el contenido de [bold]{escape(str(ruta))}[/bold]."
        )
        raise typer.Exit(1)

    if not entradas:
        consola.print(
            f"[yellow]La carpeta [bold]{escape(str(ruta))}[/bold] está vacía.[/yellow]"
        )
        return

    # Se lee cada entrada una sola vez; las que fallen (permisos, enlace roto)
    # se omiten y se avisa al final, sin cortar el listado.
    legibles: list[tuple[bool, str, object]] = []
    omitidas = 0
    for entrada in entradas:
        try:
            datos = entrada.stat()
            legibles.append((entrada.is_dir(), entrada.name, datos))
        except OSError:
            omitidas += 1

    if not legibles:
        consola_errores.print(
            "[red]Error:[/red] no se ha podido leer ninguna entrada de la carpeta."
        )
        raise typer.Exit(1)

    # Carpetas primero y, dentro de cada grupo, alfabético sin mirar mayúsculas.
    legibles.sort(key=lambda item: (not item[0], item[1].casefold()))

    tabla = Table(title=f"Contenido de {escape(str(ruta))}")
    tabla.add_column("Nombre")
    tabla.add_column("Tipo")
    tabla.add_column("Tamaño", justify="right")
    tabla.add_column("Modificado")

    for es_carpeta, nombre, datos in legibles:
        tamano = "—" if es_carpeta else _tamano_legible(datos.st_size)
        modificado = datetime.fromtimestamp(datos.st_mtime).strftime("%Y-%m-%d %H:%M")
        tabla.add_row(escape(nombre), _tipo(nombre, es_carpeta), tamano, modificado)

    consola.print(tabla)

    if omitidas:
        detalle = "una entrada omitida" if omitidas == 1 else f"{omitidas} entradas omitidas"
        consola_errores.print(
            f"[yellow]Aviso:[/yellow] {detalle}: no se pudo leer su tamaño o fecha."
        )


def _tamano_legible(nbytes: int) -> str:
    """Convierte un tamaño en bytes a la unidad más cómoda: B, KiB, MiB, GiB o TiB."""
    tamano = float(nbytes)
    unidad = "B"
    for unidad_siguiente in ("KiB", "MiB", "GiB", "TiB"):
        if tamano < 1024:
            break
        tamano /= 1024
        unidad = unidad_siguiente
    if unidad == "B":
        return f"{int(tamano)} {unidad}"
    return f"{tamano:.1f} {unidad}"


def _tipo(nombre: str, es_carpeta: bool) -> str:
    """Devuelve «carpeta», la extensión en minúsculas o «sin extensión»."""
    if es_carpeta:
        return "carpeta"
    extension = Path(nombre).suffix.lstrip(".").lower()
    return extension if extension else "sin extensión"
