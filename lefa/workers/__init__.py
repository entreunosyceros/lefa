"""
Workers en segundo plano (QThread).

Desacoplan operaciones potencialmente lentas (PDF, SMTP, exportaciones)
del hilo principal de la interfaz gráfica.
"""

from lefa.workers.pdf_worker import PDFWorker
from lefa.workers.smtp_worker import SMTPWorker

__all__ = ["PDFWorker", "SMTPWorker"]
