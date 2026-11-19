"""Pruebas de IA: a_nombre_seguro, Resumir y RenombrarIA con proveedor falso,
y la gestión de errores de ProveedorCentro sin red real.
"""

import pytest

from tareas.acciones import Resumir, RenombrarIA, a_nombre_seguro
from tareas.errores import IANoDisponible
from tareas.ia import ProveedorCentro


def _config_ia(tipo: str, nombre: str, **cambios) -> dict:
    """Configuración mínima de una acción de IA; los casos cambian lo que necesitan."""
    base = {
        "nombre": nombre,
        "tipo": tipo,
        "descripcion": "Acción de prueba con IA.",
        "instrucciones": "Instrucciones de prueba.",
        "max_caracteres": 12000,
    }
    base.update(cambios)
    return base


@pytest.mark.parametrize(
    ("respuesta", "esperado"),
    [
        ("Tema 3: ¡Linux & Bash!", "tema-3-linux-bash"),
        ("../../etc/passwd", "etc-passwd"),
        ("Informe de la semana.pdf", "informe-de-la-semana"),
        ("", ""),
    ],
    ids=["tildes-y-signos", "ruta-trasera", "extension-pdf", "respuesta-vacia"],
)
def test_a_nombre_seguro(respuesta: str, esperado: str) -> None:
    """El nombre seguro quita tildes, signos y rutas; con respuesta vacía queda «»."""
    assert a_nombre_seguro(respuesta) == esperado


def test_resumir_escribe_md_en_resumenes_y_lleva_documento(descargas, modelo_falso):
    """Resumir con el falso escribe «factura.resumen.md» en «resumenes» y pide <documento>."""
    falso = modelo_falso("Resumen del documento de prueba.")
    # Motor no puede recibir el proveedor: se construye la acción con el falso.
    accion = Resumir(
        _config_ia("resumir", "resumir-factura", destino="resumenes"), falso
    )
    resultado = accion.aplicar(descargas / "factura.pdf", 1, simular=False)
    assert resultado.estado == "hecho"
    esperado = descargas / "resumenes" / "factura.resumen.md"
    assert resultado.destino == esperado
    assert esperado.is_file()
    assert esperado.read_text(encoding="utf-8") == "Resumen del documento de prueba."
    assert len(falso.preguntas) == 1
    assert "<documento>" in falso.preguntas[0]


def test_resumir_simular_no_pregunta_y_detalla_enviaria(descargas, modelo_falso):
    """Con simular, el modelo no se pregunta y el detalle dice «enviaría»."""
    falso = modelo_falso("texto que no se debe enviar")
    accion = Resumir(
        _config_ia("resumir", "resumir-simular", destino="resumenes"), falso
    )
    resultado = accion.aplicar(descargas / "factura.pdf", 1, simular=True)
    assert resultado.estado == "simulado"
    assert "enviaría" in resultado.detalle
    assert falso.preguntas == []
    assert not (descargas / "resumenes").exists()


def test_renombrar_ia_nombre_invalido_queda_saltado(descargas, modelo_falso):
    """Si el modelo devuelve un nombre con «..», el fichero NO se renombra."""
    falso = modelo_falso("../../.bashrc")
    accion = RenombrarIA(_config_ia("renombrar-ia", "renombrar-ia-invalido"), falso)
    fichero = descargas / "factura.pdf"
    resultado = accion.aplicar(fichero, 1, simular=False)
    assert resultado.estado == "saltado"
    assert fichero.is_file()
    assert fichero.name == "factura.pdf"


def test_renombrar_ia_nombre_bueno_conserva_extension(descargas, modelo_falso):
    """Un nombre del modelo bien formado renombra el fichero conservando la extensión."""
    falso = modelo_falso("Historial Bash")
    accion = RenombrarIA(_config_ia("renombrar-ia", "renombrar-ia-valido"), falso)
    fichero = descargas / "factura.pdf"
    resultado = accion.aplicar(fichero, 1, simular=False)
    assert resultado.estado == "hecho"
    assert resultado.destino == descargas / "historial-bash.pdf"
    assert resultado.destino.suffix == ".pdf"
    assert resultado.destino.is_file()
    assert not fichero.exists()


def test_sin_clave_de_ia_lanza_IANoDisponible():
    """Sin CENTRO_IA_URL/CENTRO_IA_KEY, se lanza IANoDisponible mencionando la clave."""
    with pytest.raises(IANoDisponible) as excinfo:
        ProveedorCentro.desde_entorno()
    assert "CENTRO_IA_KEY" in str(excinfo.value)


def test_url_inaccesible_lanza_IANoDisponible_sin_traza(monkeypatch):
    """Con una URL local cerrada, se lanza IANoDisponible sin traza."""
    monkeypatch.setenv("CENTRO_IA_URL", "http://127.0.0.1:9/v1")
    monkeypatch.setenv("CENTRO_IA_KEY", "clave-de-prueba")
    proveedor = ProveedorCentro.desde_entorno()
    with pytest.raises(IANoDisponible) as excinfo:
        proveedor.completar("sistema", "usuario")
    assert isinstance(excinfo.value, IANoDisponible)
    assert "Traceback" not in str(excinfo.value)
