"""Excepciones controladas de tareas: cada una lleva su código de salida."""

from pathlib import Path


class TareasError(Exception):
    """Error controlado de tareas: mensaje para el usuario y código de salida."""

    codigo_salida = 1

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class ConfigError(TareasError):
    """Configuración inválida: fichero ausente, JSON roto o estructura errónea."""

    codigo_salida = 3

    def __init__(self, ruta: Path, motivo: str) -> None:
        mensaje = f"configuración «{ruta}»: {motivo}"
        super().__init__(mensaje)
        self.ruta = ruta
        self.motivo = motivo


class AccionNoValida(ConfigError):
    """Un campo de una acción del fichero de configuración no cumple el esquema."""

    def __init__(self, accion: str, campo: str, motivo: str) -> None:
        mensaje = f"Acción «{accion}», campo «{campo}»: {motivo}"
        TareasError.__init__(self, mensaje)
        self.accion = accion
        self.campo = campo
        self.motivo = motivo


class IANoDisponible(TareasError):
    """El servidor de IA no está configurado, no responde o no se puede usar."""

    codigo_salida = 4
