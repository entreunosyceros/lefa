"""
Envío de facturas por correo electrónico con adjunto PDF.

Utiliza smtplib (biblioteca estándar) y la configuración SMTP del usuario.
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from lefa.models import EstadoFactura
from lefa.services.factura_service import FacturaService
from lefa.services.pdf_service import PDFService
from lefa.services.preferencias_service import PreferenciasService
from lefa.services.smtp_config_service import SeguridadSMTP, SmtpConfigService


class EmailService:
    """Envía facturas por SMTP con el PDF adjunto."""

    @staticmethod
    def enviar_factura(factura_id: int) -> str:
        config = SmtpConfigService.cargar()
        if not config.esta_configurada():
            raise ValueError(
                "Configure una cuenta de correo en Herramientas → "
                "Configurar correo electrónico…"
            )

        contrasena = SmtpConfigService.obtener_contrasena()
        if not contrasena:
            raise ValueError("No hay contraseña SMTP guardada. Vuelva a configurar el correo.")

        factura = FacturaService.obtener_por_id(factura_id)
        if factura is None:
            raise ValueError(f"Factura {factura_id} no encontrada.")

        if factura.estado == EstadoFactura.BORRADOR:
            raise ValueError("Solo se pueden enviar por email facturas emitidas o cobradas.")

        email_destino = factura.cliente.email.strip()
        if not email_destino:
            raise ValueError("El cliente no tiene email configurado.")

        pdf_path = PDFService.obtener_o_generar(factura)
        numero = factura.numero_factura or f"Borrador #{factura.id}"

        mensaje = EmailMessage()
        mensaje["Subject"] = f"Factura {numero}"
        mensaje["From"] = formataddr(
            (config.nombre_remitente or PreferenciasService.cargar().emisor_razon_social, config.remitente)
        )
        mensaje["To"] = email_destino
        mensaje.set_content(
            EmailService._cuerpo_mensaje(factura, numero)
        )

        datos_pdf = pdf_path.read_bytes()
        mensaje.add_attachment(
            datos_pdf,
            maintype="application",
            subtype="pdf",
            filename=pdf_path.name,
        )

        EmailService._enviar_smtp(config, contrasena, mensaje)

        FacturaService.marcar_enviada(factura_id, email_destino)
        return f"Factura {numero} enviada a {email_destino}"

    @staticmethod
    def _cuerpo_mensaje(factura, numero: str) -> str:
        total = factura.calcular_total()
        return (
            f"Estimado/a {factura.cliente.razon_social},\n\n"
            f"Adjunto encontrará la factura {numero} por un importe de "
            f"{total:.2f} EUR.\n\n"
            "Este mensaje ha sido enviado automáticamente desde LEFA.\n"
        )

    @staticmethod
    def _enviar_smtp(config, contrasena: str, mensaje: EmailMessage) -> None:
        host = config.servidor.strip()
        puerto = config.puerto or config.puerto_por_defecto()
        usuario = config.usuario.strip()

        if config.seguridad == SeguridadSMTP.SSL:
            with smtplib.SMTP_SSL(host, puerto, timeout=30) as servidor:
                servidor.login(usuario, contrasena)
                servidor.send_message(mensaje)
            return

        with smtplib.SMTP(host, puerto, timeout=30) as servidor:
            servidor.ehlo()
            if config.seguridad == SeguridadSMTP.STARTTLS:
                servidor.starttls()
                servidor.ehlo()
            if usuario:
                servidor.login(usuario, contrasena)
            servidor.send_message(mensaje)

    @staticmethod
    def probar_conexion(
        config,
        contrasena: str,
        destino_prueba: str | None = None,
    ) -> str:
        """Verifica credenciales SMTP; opcionalmente envía un correo de prueba."""
        host = config.servidor.strip()
        puerto = config.puerto or config.puerto_por_defecto()
        usuario = config.usuario.strip()

        if not host or not usuario or not contrasena:
            raise ValueError("Servidor, usuario y contraseña son obligatorios.")

        if config.seguridad == SeguridadSMTP.SSL:
            with smtplib.SMTP_SSL(host, puerto, timeout=30) as servidor:
                servidor.login(usuario, contrasena)
                if destino_prueba:
                    EmailService._enviar_correo_prueba(
                        servidor, config, destino_prueba
                    )
            return "Conexión SSL correcta."

        with smtplib.SMTP(host, puerto, timeout=30) as servidor:
            servidor.ehlo()
            if config.seguridad == SeguridadSMTP.STARTTLS:
                servidor.starttls()
                servidor.ehlo()
            servidor.login(usuario, contrasena)
            if destino_prueba:
                EmailService._enviar_correo_prueba(servidor, config, destino_prueba)

        if destino_prueba:
            return f"Correo de prueba enviado a {destino_prueba}."
        return "Conexión SMTP correcta."

    @staticmethod
    def _enviar_correo_prueba(servidor, config, destino: str) -> None:
        prueba = EmailMessage()
        prueba["Subject"] = "LEFA - Correo de prueba"
        prueba["From"] = formataddr(
            (config.nombre_remitente or "LEFA", config.remitente or config.usuario)
        )
        prueba["To"] = destino
        prueba.set_content(
            "Este es un correo de prueba enviado desde LEFA.\n"
            "Si lo recibe, la configuración SMTP es correcta.\n"
        )
        servidor.send_message(prueba)
