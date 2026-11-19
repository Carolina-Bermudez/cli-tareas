"""Pruebas de acciones.py: cómo se aplican las acciones a los ficheros."""

from tareas.acciones import Mover, Renombrar
from tareas.motor import Motor


def _config(tipo: str, nombre: str, **cambios) -> dict:
    """Configuración mínima de una acción; los casos cambian lo que necesitan."""
    base = {"nombre": nombre, "tipo": tipo, "descripcion": "Acción de prueba."}
    base.update(cambios)
    return base


def test_mover_solo_lo_que_cumple_el_filtro(descargas):
    """Solo se mueven los ficheros que cumplen el filtro."""
    config = _config(
        "mover",
        "mover-png-y-tmp",
        destino="PDF",
        filtro={"extensiones": [".png", ".tmp"]},
    )
    motor = Motor([config])
    ficheros = motor.seleccionar(descargas, config["filtro"])
    resultados = motor.obtener("mover-png-y-tmp").ejecutar(ficheros, simular=False)
    assert [f.name for f in ficheros] == ["cumpleaños 2.png", "viejo.tmp"]
    assert [r.estado for r in resultados] == ["hecho", "hecho"]
    pdf = descargas / "PDF"
    assert (pdf / "cumpleaños 2.png").is_file()
    assert (pdf / "viejo.tmp").is_file()
    assert not (descargas / "cumpleaños 2.png").exists()
    assert not (descargas / "viejo.tmp").exists()
    # No cumplen el filtro: siguen en su carpeta.
    assert (descargas / "factura.pdf").is_file()
    assert (descargas / "FOTO1.JPG").is_file()


def test_simular_no_toca_el_disco(descargas):
    """Con simular=True no se mueve nada ni se crea la carpeta «PDF»."""
    config = _config("mover", "mover-simular", destino="PDF")
    resultado = Mover(config).aplicar(descargas / "factura.pdf", 1, simular=True)
    assert resultado.estado == "simulado"
    assert resultado.destino == descargas / "PDF" / "factura.pdf"
    assert (descargas / "factura.pdf").is_file()
    assert not (descargas / "PDF").exists()


def test_mover_no_sobrescribe_factura(descargas):
    """Si ya hay «factura.pdf» en «PDF», el movido se guarda como «factura (1).pdf»."""
    pdf = descargas / "PDF"
    pdf.mkdir()
    (pdf / "factura.pdf").write_text("ya existe", encoding="utf-8")
    config = _config("mover", "mover-factura", destino="PDF")
    resultado = Mover(config).aplicar(descargas / "factura.pdf", 1, simular=False)
    assert resultado.estado == "hecho"
    assert resultado.destino == pdf / "factura (1).pdf"
    assert (pdf / "factura.pdf").read_text(encoding="utf-8") == "ya existe"
    assert (pdf / "factura (1).pdf").is_file()
    assert not (descargas / "factura.pdf").exists()


def test_jpg_en_mayusculas_cuenta(descargas):
    """FOTO1.JPG cuenta como «.jpg» para el filtro de extensiones."""
    motor = Motor([_config("mover", "mover-jpg", destino="PDF")])
    seleccionados = motor.seleccionar(descargas, {"extensiones": [".jpg"]})
    assert seleccionados == [descargas / "FOTO1.JPG"]


def test_borrar_solo_lo_viejo(descargas):
    """Borrar se aplica solo a los ficheros más antiguos que el filtro."""
    config = _config("borrar", "borrar-viejos", filtro={"mas_antiguo_que_dias": 30})
    motor = Motor([config])
    ficheros = motor.seleccionar(descargas, config["filtro"])
    resultados = motor.obtener("borrar-viejos").ejecutar(ficheros, simular=False)
    assert [f.name for f in ficheros] == ["viejo.tmp"]
    assert [r.estado for r in resultados] == ["hecho"]
    assert not (descargas / "viejo.tmp").exists()
    # Lo que no es viejo sigue ahí: siguen en su carpeta.
    assert (descargas / "factura.pdf").is_file()
    assert (descargas / "cumpleaños 2.png").is_file()


def test_renombrar_con_plantilla(descargas):
    """Renombrar aplica la plantilla del fichero."""
    config = _config(
        "renombrar", "renombrar-trabajo", plantilla="{nombre}-trabajo{ext}"
    )
    resultado = Renombrar(config).aplicar(
        descargas / "apuntes de redes.docx", 1, simular=False
    )
    assert resultado.estado == "hecho"
    assert resultado.destino == descargas / "apuntes de redes-trabajo.docx"
    assert not (descargas / "apuntes de redes.docx").exists()
    assert (descargas / "apuntes de redes-trabajo.docx").is_file()
