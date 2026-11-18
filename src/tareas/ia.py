"""Capa de IA: proveedores de modelos y respuestas, separada de la CLI."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import os
from pathlib import Path
import ssl
import time

import httpx
from dotenv import find_dotenv, load_dotenv

from tareas.errores import IANoDisponible

# Modelo usado si CENTRO_IA_MODELO no está definido en el entorno.
_MODELO_POR_DEFECTO = "qwen3.8-flash-next"
_FALTA_CONFIGURACION = (
    "Faltan CENTRO_IA_URL o CENTRO_IA_KEY: ponlas en .env (mira .env.example)"
)


@dataclass
class Respuesta:
    """Texto devuelto por el modelo y coste de la llamada."""

    texto: str
    tokens_entrada: int
    tokens_salida: int
    segundos: float

    def resumen(self) -> str:
        """Devuelve un resumen breve de tokens y tiempo de la llamada."""
        return f"{self.tokens_entrada}+{self.tokens_salida} tokens · {self.segundos:.1f} s"


class ProveedorIA(ABC):
    """Interfaz común de cualquier proveedor de IA."""

    @abstractmethod
    def completar(self, sistema: str, usuario: str, max_tokens: int = 800) -> Respuesta:
        """Pide una respuesta al modelo con un mensaje de sistema y otro de usuario."""


class ProveedorCentro(ProveedorIA):
    """Servidor de IA del centro, con API compatible con OpenAI."""

    def __init__(self, url: str, clave: str, modelo: str, contexto: ssl.SSLContext) -> None:
        self.url = url.rstrip("/")
        self.modelo = modelo
        # Privado y sin repr: la clave nunca debe aparecer en pantalla ni en logs.
        self._clave = clave
        self._contexto = contexto

    @staticmethod
    def desde_entorno() -> "ProveedorCentro":
        """Lee .env (o las variables ya exportadas) y crea el proveedor."""
        load_dotenv(find_dotenv(usecwd=True))
        url = os.environ.get("CENTRO_IA_URL", "").strip()
        clave = os.environ.get("CENTRO_IA_KEY", "").strip()
        if not url or not clave:
            raise IANoDisponible(_FALTA_CONFIGURACION)

        modelo = os.environ.get("CENTRO_IA_MODELO", "").strip() or _MODELO_POR_DEFECTO
        ruta_ca = os.environ.get("CENTRO_IA_CA", "").strip()
        return ProveedorCentro(url, clave, modelo, _contexto_ssl(ruta_ca))

    def completar(self, sistema: str, usuario: str, max_tokens: int = 800) -> Respuesta:
        """Llama a /chat/completions y convierte cualquier fallo en IANoDisponible."""
        cuerpo = {
            "model": self.modelo,
            "messages": [
                {"role": "system", "content": sistema},
                {"role": "user", "content": usuario},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.2,
        }
        cabeceras = {
            "Authorization": f"Bearer {self._clave}",
            "Content-Type": "application/json",
        }
        inicio = time.perf_counter()
        try:
            with httpx.Client(verify=self._contexto, timeout=httpx.Timeout(60, connect=5)) as cliente:
                respuesta = cliente.post(
                    f"{self.url}/chat/completions",
                    json=cuerpo,
                    headers=cabeceras,
                )
                respuesta.raise_for_status()
            segundos = time.perf_counter() - inicio

            datos = respuesta.json()
            texto = datos["choices"][0]["message"]["content"]
            if not isinstance(texto, str):
                raise IANoDisponible("La respuesta del servidor de IA no tenía texto.")
            uso = datos.get("usage", {})
            tokens_entrada = int(uso.get("prompt_tokens", 0))
            tokens_salida = int(uso.get("completion_tokens", 0))
            return Respuesta(texto, tokens_entrada, tokens_salida, max(segundos, 0.0))
        except IANoDisponible:
            raise
        except httpx.HTTPStatusError as exc:
            codigo = exc.response.status_code
            if codigo in (401, 403):
                raise IANoDisponible(
                    f"CENTRO_IA_KEY no es válida o no tiene permisos (HTTP {codigo})."
                ) from None
            if codigo == 429:
                raise IANoDisponible(
                    "El servidor de IA está saturado (HTTP 429). Espera antes de volver a intentarlo."
                ) from None
            if codigo >= 500:
                raise IANoDisponible(
                    f"El servidor de IA falló (HTTP {codigo}). Inténtalo más tarde."
                ) from None
            raise IANoDisponible(
                f"El servidor de IA rechazó la petición (HTTP {codigo})."
            ) from None
        except httpx.TimeoutException:
            raise IANoDisponible(
                "El servidor de IA tardó demasiado en responder. Inténtalo de nuevo."
            ) from None
        except httpx.ConnectError as exc:
            if _es_de_certificado(exc):
                raise IANoDisponible(
                    "No me fío del servidor: falta el certificado del centro (CENTRO_IA_CA)"
                ) from None
            raise IANoDisponible(
                "No se pudo conectar con el servidor de IA. Comprueba CENTRO_IA_URL "
                "y que el servicio esté encendido."
            ) from None
        except ssl.SSLError as exc:
            if _es_de_certificado(exc):
                raise IANoDisponible(
                    "No me fío del servidor: falta el certificado del centro (CENTRO_IA_CA)"
                ) from None
            raise IANoDisponible("No se pudo establecer la conexión segura con el servidor de IA.") from None
        except (KeyError, IndexError, TypeError, ValueError):
            raise IANoDisponible(
                "El servidor de IA no devolvió una respuesta JSON válida o le faltaban datos."
            ) from None
        except httpx.HTTPError:
            raise IANoDisponible(
                "No se pudo hablar con el servidor de IA. Inténtalo de nuevo."
            ) from None
        except Exception:
            # Red de seguridad: en la CLI nunca debe aparecer una traza.
            raise IANoDisponible("Fallo inesperado al hablar con el servidor de IA.") from None


def _es_de_certificado(exc: Exception) -> bool:
    """Detecta los errores TLS de certificado, que httpx envuelve en ConnectError."""
    return "CERTIFICATE" in str(exc).upper()


def _contexto_ssl(ruta_ca: str) -> ssl.SSLContext:
    """Usa la CA del centro si se indicó; si no, las certificadas del sistema."""
    if not ruta_ca:
        return ssl.create_default_context()
    ruta = Path(ruta_ca).expanduser()
    try:
        return ssl.create_default_context(cafile=str(ruta))
    except (OSError, ValueError, ssl.SSLError):
        raise IANoDisponible(
            f"No se pudo leer el certificado del centro (CENTRO_IA_CA): «{ruta}»"
        ) from None
