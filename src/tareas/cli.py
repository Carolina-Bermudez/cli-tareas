"""Órdenes de la CLI de tareas: version y listar."""

from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from tareas import __version__

app = typer.Typer(
    help="Automatiza tareas repetitivas con ficheros desde la terminal.",
    no_args_is_help=True,
    add_completion=False,
)

consola = Console()
consola_errores = Console(stderr=True)


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
