"""
Diálogo de documentación de usuario — qué hace LEFA y cómo usarlo.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QTextBrowser, QVBoxLayout

from lefa import __app_name__, __version__


def _contenido_html() -> str:
    return f"""
<h1 style="margin-top:0;">Guía de uso de {__app_name__}</h1>
<p>Versión {__version__} — facturación local para autónomos (Linux y Windows).</p>

<h2>1. Primeros pasos</h2>
<ol>
<li><b>Herramientas → Preferencias…</b> — Configure IVA, IRPF, datos del emisor (nombre, NIF, dirección, <b>IBAN</b>), logotipo, formato de numeración y series.</li>
<li><b>Herramientas → Configurar correo electrónico…</b> — Solo si va a enviar facturas por email (SMTP y contraseña en el llavero del sistema).</li>
<li><b>Clientes → Nuevo cliente…</b> o pestaña <b>Clientes</b> — Alta de clientes con NIF. Para administraciones públicas (FACe), rellene los códigos DIR3 en la ficha del cliente.</li>
<li>Cree su primera factura en la pestaña <b>Nueva Factura</b> y pulse <b>Emitir Factura</b>.</li>
</ol>

<h2>2. Pestañas principales</h2>
<p>Empiece en <b>Inicio</b>: verá el flujo en línea recta (cliente → líneas → emitir → listo) sin saltar entre ventanas como en un ERP tradicional.</p>
<table border="0" cellpadding="6" cellspacing="0">
<tr><td><b>Inicio</b></td><td>Mapa visual del camino recto y accesos rápidos.</td></tr>
<tr><td><b>Nueva Factura</b></td><td>Crear borradores, emitir, generar PDF/XML y enviar por correo.</td></tr>
<tr><td><b>Nuevo Presupuesto</b></td><td>Ofertas comerciales sin validez fiscal (PDF al cliente).</td></tr>
<tr><td><b>Listado presupuestos</b></td><td>Aceptar, convertir en factura, rechazar o ver la factura asociada.</td></tr>
<tr><td><b>Listado</b></td><td>Consultar facturas emitidas: duplicar, rectificar, marcar cobrada, ver envío y vencimiento.</td></tr>
<tr><td><b>Clientes</b></td><td>Buscar, editar y ver historial de facturación por cliente.</td></tr>
</table>

<h2>3. Facturas</h2>
<h3>Crear y emitir</h3>
<ol>
<li>Seleccione <b>cliente</b> y <b>serie</b> (FACT, RECT, etc.).</li>
<li>Añada líneas manualmente, desde <b>plantilla</b>, <b>servicio</b> o <b>plantilla de factura completa</b>.</li>
<li>Ajuste IVA e IRPF si hace falta.</li>
<li><b>Guardar como Borrador</b> — editable, sin número oficial.</li>
<li><b>Emitir Factura</b> — asigna número, genera PDF, XML Facturae, registro VeriFactu y QR en el PDF. La factura queda bloqueada.</li>
</ol>
<h3>Enviar por email</h3>
<p>Tras emitir, use <b>Enviar por email</b> (requiere SMTP configurado y email del cliente). El listado muestra si ya se envió.</p>
<h3>Duplicar</h3>
<p>En <b>Listado</b>, seleccione una factura emitida o cobrada y pulse <b>Duplicar</b>. Se abre un borrador nuevo con los mismos datos y vencimiento recalculado.</p>
<h3>Rectificar</h3>
<p>En <b>Listado</b>, pulse <b>Rectificar</b> sobre una factura emitida. Se crea un borrador en serie <b>RECT</b> vinculado a la original. Ajuste líneas (importes negativos si procede) y emita.</p>
<h3>Marcar como cobrada</h3>
<p>En <b>Listado</b>, seleccione una factura emitida y pulse <b>Marcar como Cobrada</b>.</p>

<h2>4. Presupuestos</h2>
<ol>
<li><b>Nuevo Presupuesto</b> — cliente, líneas, <b>Emitir presupuesto</b> (genera PDF).</li>
<li><b>Listado presupuestos → Aceptar</b> cuando el cliente confirme.</li>
<li><b>Convertir en factura</b> — crea un borrador en Nueva Factura y marca el presupuesto como <i>Convertido</i>.</li>
<li>Meses después, use <b>Ver factura asociada</b> en un presupuesto convertido para ir directo a esa factura.</li>
</ol>
<p>Estados: Borrador → Emitido → Aceptado → Convertido (o Rechazado).</p>

<h2>5. Clientes</h2>
<ul>
<li><b>Menú Clientes → Nuevo cliente…</b> o pestaña <b>Clientes</b>.</li>
<li>Busque por nombre, NIF o email en la pestaña Clientes.</li>
<li>Al editar un cliente verá sus facturas y el total facturado.</li>
<li>Sección <b>Facturae / FACe</b>: IBAN del cliente (opcional), forma de pago (04 = transferencia) y códigos DIR3 para facturar a la administración pública.</li>
</ul>

<h2>6. Menú Herramientas</h2>
<ul>
<li><b>Configurar correo electrónico…</b> — Cuenta SMTP para envío de facturas.</li>
<li><b>Preferencias…</b> — Impuestos, emisor, IBAN, numeración, series, carpeta PDF, logotipo.</li>
<li><b>Plantillas de líneas…</b> — Conceptos recurrentes (descripción, cantidad, precio).</li>
<li><b>Plantillas de factura…</b> — Facturas completas reutilizables.</li>
<li><b>Catálogo de servicios…</b> — Servicios con precio e IVA para añadir con un clic.</li>
<li><b>Exportar registros VeriFactu…</b> — ZIP con la cadena de registros para auditoría.</li>
</ul>

<h2>7. Archivo</h2>
<ul>
<li><b>Crear copia de seguridad…</b> — ZIP con base de datos, PDFs, XML, registros VeriFactu y configuración (la contraseña SMTP no se incluye: está en el llavero).</li>
<li><b>Salir</b> (<kbd>Ctrl+Q</kbd>) — Cierra la aplicación por completo.</li>
</ul>

<h2>8. VeriFactu y Facturae</h2>
<p>Al <b>emitir</b>, LEFA genera automáticamente:</p>
<ul>
<li><b>PDF</b> con logotipo y código QR tributario (URL oficial AEAT: NIF, número, fecha e importe).</li>
<li><b>XML Facturae</b> en <code>~/.lefa/facturas_xml/</code> — incluye IBAN del emisor y, si aplica, códigos DIR3 del cliente.</li>
<li><b>Registro VeriFactu</b> encadenado (hash SHA-256 único para todas las series, incluidas rectificativas).</li>
</ul>

<h2>9. Dónde se guardan los datos</h2>
<p>Todo queda en su equipo, en la carpeta <code>~/.lefa/</code> (en Windows: <code>%USERPROFILE%\\.lefa\\</code>): base de datos, PDFs, XML, preferencias y registros VeriFactu.</p>
<p><i>Nota:</i> el envío de correo usa el llavero del sistema; requiere un entorno de escritorio activo (no funciona en servidores sin interfaz gráfica).</p>

<h2>10. Bandeja del sistema</h2>
<p>Si hay icono en la bandeja, cerrar la ventana con la X <b>oculta</b> LEFA (sigue en segundo plano). Para salir del todo: <b>Archivo → Salir</b> o <i>Salir</i> en el menú de la bandeja. Doble clic en el icono restaura la ventana.</p>
"""


class DocumentacionDialog(QDialog):
    """Ventana modal con la guía de uso integrada."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Ayuda rápida — {__app_name__}")
        self.setMinimumSize(720, 520)
        self.resize(800, 600)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        visor = QTextBrowser()
        visor.setOpenExternalLinks(True)
        visor.setHtml(_contenido_html())
        visor.setStyleSheet(
            "QTextBrowser { font-size: 13px; line-height: 1.4; padding: 8px; }"
        )
        layout.addWidget(visor)

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)
