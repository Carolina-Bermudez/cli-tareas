"""Pruebas de la CLI con typer.testing.CliRunner: salida y mensajes por código."""

from typer.testing import CliRunner

from tareas.cli import app

runner = CliRunner()

# Acción «resumir» mínima válida; necesita «descripcion» e «instrucciones».
ACCION_RESUMIR = {
    "nombre": "resumir",
    "tipo": "resumir",
    "descripcion": "Resume un fichero con IA.",
    "instrucciones": "Resume el documento.",
}


def salida(result) -> str:
    """Todo lo que apareció en la salida: stdout y stderr según la versión."""
    try:
        stderr = result.stderr
    except (AttributeError, ValueError):
        stderr = ""
    return f"{result.output or ''}\n{stderr or ''}"


def test_salida_0_help_funciona():
    """tareas --help sale con código 0 y muestra la ayuda de la app."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Automatiza tareas repetitivas" in salida(result)


def test_salida_1_accion_que_no_existe(escribir_config):
    """Ejecutar una acción desconocida sale con código 1."""
    ruta = escribir_config({"version": 1, "acciones": [ACCION_RESUMIR]})
    result = runner.invoke(app, ["--config", ruta.name, "ejecutar", "nope"])
    assert result.exit_code == 1
    assert "la acción «nope» no existe" in salida(result)


def test_salida_2_opcion_que_no_existe():
    """Una opción desconocida sale con código 2 (error de uso)."""
    result = runner.invoke(app, ["listar", "--inventada"])
    assert result.exit_code == 2
    assert "inventada" in salida(result)


def test_salida_3_json_roto_en_validar(escribir_config):
    """--config con JSON roto en validar sale con código 3 sin trazas."""
    ruta = escribir_config('{"version": 1, "acciones": }')
    result = runner.invoke(app, ["--config", ruta.name, "validar"])
    assert result.exit_code == 3
    assert "no es JSON válido" in salida(result)
    assert "Traceback" not in salida(result)


def test_salida_4_resumir_sin_clave(escribir_config):
    """ejecutar resumir sin CENTRO_IA_URL ni CENTRO_IA_KEY sale con código 4."""
    ruta = escribir_config({"version": 1, "acciones": [ACCION_RESUMIR]})
    result = runner.invoke(app, ["--config", ruta.name, "ejecutar", "resumir"])
    assert result.exit_code == 4
    assert "siguen funcionando" in salida(result)
