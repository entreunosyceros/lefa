# Instalación

[← Índice](README.md) · [Interfaz](interfaz.md) · [Flujos operativos](flujos-operativos.md)

## Ejecución rápida (recomendada)

`run_app.py` crea el entorno virtual si no existe, instala dependencias y arranca la aplicación:

```bash
cd LEFA
python3 run_app.py
```

En Windows:

```powershell
cd LEFA
python run_app.py
```

## Requisitos en Linux (PyQt6)

Desde **Qt 6.5**, el plugin gráfico `xcb` exige la biblioteca del sistema **libxcb-cursor**. Si al arrancar aparece un error del tipo *Could not load the Qt platform plugin "xcb"* o *xcb-cursor0 is needed*, instale el paquete antes de volver a ejecutar:

```bash
# Debian / Ubuntu / Mint
sudo apt install libxcb-cursor0

# Fedora
sudo dnf install xcb-util-cursor

# Arch
sudo pacman -S xcb-util-cursor
```

`run_app.py` detecta esta dependencia y muestra estas instrucciones si falta.

## Instalación manual

```bash
cd LEFA
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Variables de entorno (opcionales)

| Variable            | Descripción |
|---------------------|-------------|
| `LEFA_PROJECT_DIR`  | Raíz del proyecto (p. ej. instalaciones empaquetadas) |
| `LEFA_VENV`         | Ruta explícita al entorno virtual |

## Ver también

- [Datos locales y copias de seguridad](datos-y-backup.md)
- [Arquitectura del proyecto](arquitectura.md)
