"""
Persistencia de la configuración SMTP del usuario.

La contraseña se guarda en el llavero del sistema (keyring), no en disco en texto plano.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum

import keyring

from lefa.config import KEYRING_SERVICE, KEYRING_USER, SMTP_CONFIG_PATH, ensure_directories


class SeguridadSMTP(str, Enum):
    """Modo de conexión segura con el servidor SMTP."""

    STARTTLS = "starttls"  # Puerto 587 habitual
    SSL = "ssl"            # Puerto 465 habitual
    NINGUNA = "ninguna"    # Sin cifrado (solo redes de confianza)


@dataclass
class SmtpConfig:
    """Parámetros de la cuenta de correo para envío de facturas."""

    servidor: str = ""
    puerto: int = 587
    seguridad: SeguridadSMTP = SeguridadSMTP.STARTTLS
    usuario: str = ""
    remitente: str = ""
    nombre_remitente: str = ""

    def esta_configurada(self) -> bool:
        """Comprueba si hay datos mínimos y contraseña guardada."""
        if not self.servidor.strip() or not self.usuario.strip() or not self.remitente.strip():
            return False
        return SmtpConfigService.obtener_contrasena() is not None

    def puerto_por_defecto(self) -> int:
        if self.seguridad == SeguridadSMTP.SSL:
            return 465
        if self.seguridad == SeguridadSMTP.STARTTLS:
            return 587
        return self.puerto or 25


class SmtpConfigService:
    """Carga y guarda la configuración SMTP local."""

    @staticmethod
    def cargar() -> SmtpConfig:
        ensure_directories()
        if not SMTP_CONFIG_PATH.is_file():
            return SmtpConfig()

        datos = json.loads(SMTP_CONFIG_PATH.read_text(encoding="utf-8"))
        seguridad = datos.get("seguridad", SeguridadSMTP.STARTTLS.value)
        try:
            modo = SeguridadSMTP(seguridad)
        except ValueError:
            modo = SeguridadSMTP.STARTTLS

        return SmtpConfig(
            servidor=datos.get("servidor", ""),
            puerto=int(datos.get("puerto", 587)),
            seguridad=modo,
            usuario=datos.get("usuario", ""),
            remitente=datos.get("remitente", ""),
            nombre_remitente=datos.get("nombre_remitente", ""),
        )

    @staticmethod
    def guardar(config: SmtpConfig, contrasena: str | None = None) -> None:
        """Persiste la configuración; la contraseña va al llavero si se proporciona."""
        ensure_directories()
        payload = {
            "servidor": config.servidor.strip(),
            "puerto": config.puerto,
            "seguridad": config.seguridad.value,
            "usuario": config.usuario.strip(),
            "remitente": config.remitente.strip(),
            "nombre_remitente": config.nombre_remitente.strip(),
        }
        SMTP_CONFIG_PATH.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        if contrasena is not None and contrasena != "":
            keyring.set_password(KEYRING_SERVICE, KEYRING_USER, contrasena)

    @staticmethod
    def obtener_contrasena() -> str | None:
        try:
            return keyring.get_password(KEYRING_SERVICE, KEYRING_USER)
        except Exception:
            return None

    @staticmethod
    def eliminar_contrasena() -> None:
        try:
            keyring.delete_password(KEYRING_SERVICE, KEYRING_USER)
        except Exception:
            pass

    @staticmethod
    def tiene_contrasena_guardada() -> bool:
        return SmtpConfigService.obtener_contrasena() is not None
