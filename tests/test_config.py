"""Pruebas de config.py: la configuración de acciones.json se valida al cargar."""

import pytest

from tareas.config import cargar
from tareas.errores import AccionNoValida, ConfigError


def _accion(**cambios) -> dict:
    """Acción mínima válida; cada caso prueba qué cambia."""
    base = {
        "nombre": "apartar-copias",
        "tipo": "mover",
        "destino": "PDF",
        "descripcion": "Mueve los ficheros a la subcarpeta «PDF».",
    }
    base.update(cambios)
    return base


def test_config_buena_carga(escribir_config):
    """Una configuración correcta se carga sin errores."""
    ruta = escribir_config({"version": 1, "acciones": [_accion()]})
    acciones = cargar(ruta)
    assert [a["nombre"] for a in acciones] == ["apartar-copias"]
    assert acciones[0]["tipo"] == "mover"
    assert acciones[0]["destino"] == "PDF"


@pytest.mark.parametrize(
    ("acciones", "campo"),
    [
        pytest.param([_accion(tipo="fusionar")], "tipo", id="tipo-inexistente"),
        pytest.param([_accion(destino="")], "destino", id="destino-vacío"),
        pytest.param(
            [{k: v for k, v in _accion().items() if k != "descripcion"}],
            "descripcion",
            id="sin-descripcion",
        ),
        pytest.param([_accion(filtro={"patron": "(a"})], "filtro", id="regex-rota"),
        pytest.param([_accion(destino="/PDF")], "destino", id="destino-absoluto"),
        pytest.param(
            [_accion(tipo="renombrar-ia")], "destino", id="renombrar-ia-con-destino"
        ),
        pytest.param([_accion(), _accion()], "nombre", id="nombre-repetido"),
    ],
)
def test_config_incorrecta_se_rechaza(acciones, campo, escribir_config):
    """Cada fallo de una acción se rechaza indicando el campo que falla."""
    ruta = escribir_config({"version": 1, "acciones": acciones})
    with pytest.raises(AccionNoValida) as exc:
        cargar(ruta)
    assert exc.value.campo == campo


def test_destino_con_virgulilla_se_rechaza(escribir_config):
    """Un destino «~/PDF» (a la carpeta del usuario) se rechaza."""
    ruta = escribir_config({"version": 1, "acciones": [_accion(destino="~/PDF")]})
    with pytest.raises(AccionNoValida) as exc:
        cargar(ruta)
    assert exc.value.campo == "destino"


def test_json_roto_dice_la_linea(escribir_config):
    """Un JSON que no se puede parsear señala la línea del error."""
    texto = '{"version": 1,\n"acciones": }'
    ruta = escribir_config(texto)
    with pytest.raises(ConfigError) as exc:
        cargar(ruta)
    assert "línea 2" in exc.value.motivo


def test_fichero_que_no_existe_da_error(tmp_path):
    """Un fichero que no existe da error al cargar."""
    with pytest.raises(ConfigError) as exc:
        cargar(tmp_path / "acciones.json")
    assert "no existe" in exc.value.motivo


def test_lista_de_acciones_vacía_da_error(escribir_config):
    """Una lista de acciones vacía da error al cargar."""
    ruta = escribir_config({"version": 1, "acciones": []})
    with pytest.raises(ConfigError) as exc:
        cargar(ruta)
    assert "vacía" in exc.value.motivo
