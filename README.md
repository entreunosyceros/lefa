# LEFA — Local & Eficiente Facturación para Autónomos

<p align="center">
<img width="1200" height="655" alt="logo" src="https://github.com/user-attachments/assets/d3e52c55-7abb-4cc4-bb1f-cf7640292f74" />
<br><br>
<a href="https://mintlify.wiki/entreunosyceros/lefa"><img src="https://img.shields.io/badge/Documentación_web-lefa-0891B2?style=for-the-badge&logo=readthedocs&logoColor=white" alt="Documentación web"></a>
<a href="docs/README.md"><img src="https://img.shields.io/badge/Docs_repositorio-docs-43A047?style=for-the-badge&logo=github&logoColor=white" alt="Docs del repositorio"></a>
<br>
<a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+"></a>
<a href="https://www.riverbankcomputing.com/software/pyqt/"><img src="https://img.shields.io/badge/PyQt6-escritorio-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="PyQt6"></a>
<a href="https://www.sqlite.org/"><img src="https://img.shields.io/badge/SQLite-SQLAlchemy-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"></a>
<a href="LICENSE"><img src="https://img.shields.io/github/license/entreunosyceros/lefa?style=for-the-badge" alt="Licencia GPL-3.0"></a>
<br>
<a href="docs/instalacion.md"><img src="https://img.shields.io/badge/Plataforma-Linux%20%7C%20Windows-333333?style=for-the-badge&logo=linux&logoColor=white" alt="Linux y Windows"></a>
<a href="docs/verifactu.md"><img src="https://img.shields.io/badge/VeriFactu-SIF%20(España)-C4122E?style=for-the-badge" alt="VeriFactu"></a>
<a href="docs/facturae.md"><img src="https://img.shields.io/badge/Facturae-XML-F5A623?style=for-the-badge" alt="Facturae"></a>
<a href="#estado-del-proyecto"><img src="https://img.shields.io/badge/Estado-beta-orange?style=for-the-badge" alt="Beta"></a>
</p>

Aplicación de escritorio para facturación de autónomos con **control total local**. Compatible con **Linux** y **Windows**. Sin suscripciones ni dependencia de la nube.

## ¿Por qué?

LEFA nace para autónomos que solo necesitan **gestionar clientes y emitir facturas** sin aprender un ERP completo. Todo funciona en local: SQLite, PDFs, XML Facturae y registros VeriFactu en tu equipo.

## Estado del proyecto

> LEFA se encuentra en **fase beta** de desarrollo y pruebas. Implementa los requisitos técnicos de encadenamiento y generación de registros exigidos por la normativa de sistemas de facturación en España (SIF / VeriFactu): hash encadenado, QR tributario y leyenda legal en el PDF. El **uso para facturación real corre bajo responsabilidad del usuario** hasta que se libere la versión **1.0** estable.

## Qué incluye

- Facturas: borrador → emitir → cobrar, rectificativas y duplicados
- Presupuestos convertibles en factura con un clic
- PDF + XML Facturae + registro VeriFactu/SIF al emitir
- Envío de facturas por correo (SMTP)
- Copias de seguridad en ZIP
- Series múltiples, plantillas y catálogo de servicios

## Inicio rápido

```bash
cd LEFA
python3 run_app.py
```

En Windows: `python run_app.py`

Guía completa de instalación y dependencias Linux en [docs/instalacion.md](docs/instalacion.md).

## Documentación

| Recurso | Enlace |
|---------|--------|
| **Índice de guías** (repositorio) | [docs/README.md](docs/README.md) |
| **Documentación web** (Mintlify) | [mintlify.wiki/entreunosyceros/lefa](https://mintlify.wiki/entreunosyceros/lefa) |
| Instalación | [docs/instalacion.md](docs/instalacion.md) |
| Flujos de uso | [docs/flujos-operativos.md](docs/flujos-operativos.md) |
| VeriFactu / SIF | [docs/verifactu.md](docs/verifactu.md) |

## Repositorio

Esto es un programa creado para hacer más sencilla la vida de los pequeño autónomos.

[https://github.com/entreunosyceros/lefa](https://github.com/entreunosyceros/lefa)

## Licencia

[GNU General Public License v3.0](LICENSE)
