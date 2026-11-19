"""Fixtures compartidas: todo sucede dentro de tmp_path y sin red."""

import json
import os
import time
from pathlib import Path

import pytest

from tareas.ia import ProveedorIA, Respuesta
import tareas.ia as ia


@pytest.fixture(autouse=True)
def aislado(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Aísla cwd, carpetas de usuario y entorno de IA.

    Con find_dotenv devolviendo una cadena vacía, load_dotenv("") no lee
    ningún fichero: el .env real queda fuera de alcance para toda la suite.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    for variable in (
        "CENTRO_IA_URL",
        "CENTRO_IA_KEY",
        "CENTRO_IA_MODELO",
        "CENTRO_IA_CA",
    ):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setattr(ia, "find_dotenv", lambda *args, **kwargs: "")


@pytest.fixture
def descargas(tmp_path: Path) -> Path:
    """Carpeta de trabajo con cinco ficheros; «viejo.tmp» tiene 40 días."""
    carpeta = tmp_path / "Descargas"
    carpeta.mkdir()

    # PDF válido para que pypdf pueda leerlo en las pruebas de IA.
    from pypdf import PdfWriter

    escritor = PdfWriter()
    escritor.add_blank_page(width=200, height=200)
    with (carpeta / "factura.pdf").open("wb") as fichero:
        escritor.write(fichero)

    textos = {
        "apuntes de redes.docx": "Apuntes de redes: TCP/IP, DNS y CLI.",
        "FOTO1.JPG": "contenido de foto",
        "cumpleaños 2.png": "contenido de foto",
        "viejo.tmp": "temporal antiguo",
    }
    for nombre, texto in textos.items():
        (carpeta / nombre).write_text(texto, encoding="utf-8")

    antiguo = time.time() - 40 * 24 * 60 * 60
    os.utime(carpeta / "viejo.tmp", (antiguo, antiguo))
    return carpeta


@pytest.fixture
def escribir_config(tmp_path: Path):
    """Escribe acciones.json en tmp_path y devuelve su ruta.

    Acepta una lista o un dict (se vuelcan como JSON) o texto tal cual,
    para poder probar también un JSON roto.
    """

    def _escribir(contenido: list | dict | str) -> Path:
        ruta = tmp_path / "acciones.json"
        texto = (
            contenido
            if isinstance(contenido, str)
            else json.dumps(contenido, ensure_ascii=False, indent=2)
        )
        ruta.write_text(texto, encoding="utf-8")
        return ruta

    return _escribir


class ProveedorFalso(ProveedorIA):
    """Siempre responde lo mismo y guarda cada mensaje de usuario recibido."""

    def __init__(self, texto: str) -> None:
        self.texto = texto
        self.preguntas: list[str] = []

    def completar(self, sistema: str, usuario: str, max_tokens: int = 800) -> Respuesta:
        self.preguntas.append(usuario)
        return Respuesta(
            texto=self.texto,
            tokens_entrada=12,
            tokens_salida=4,
            segundos=0.2,
        )


@pytest.fixture
def modelo_falso() -> type[ProveedorFalso]:
    """Devuelve la clase para que cada prueba elija el texto de respuesta."""
    return ProveedorFalso
