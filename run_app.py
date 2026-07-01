from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Rutas base del proyecto (siempre relativas a este archivo).
PROJECT_DIR = Path(__file__).resolve().parent
REQUIREMENTS_FILE = PROJECT_DIR / "requirements.txt"
REQUIRED_PACKAGES = ("PyQt6", "SQLAlchemy", "fpdf2", "keyring")


def get_venv_dir() -> Path:
    """
    Directorio del entorno virtual.

    - Desarrollo (árbol editable): PROJECT_DIR/.venv
    - Paquete .deb (/usr/share/...): ~/.local/share/lefa/.venv
    - LEFA_VENV: ruta explícita
    """
    override = os.environ.get("LEFA_VENV")
    if override:
        return Path(override)
    local = PROJECT_DIR / ".venv"
    if os.access(PROJECT_DIR, os.W_OK):
        return local
    data_home = Path(
        os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
    )
    return data_home / "lefa" / ".venv"


def get_venv_python() -> Path:
    """Devuelve la ruta al ejecutable Python dentro del venv."""
    venv_dir = get_venv_dir()
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def is_running_in_venv() -> bool:
    """
    Comprueba si el intérprete actual pertenece al venv del proyecto.

    Se usa sys.prefix (directorio del entorno activo), NO sys.executable.resolve(),
    porque en Linux el binario del venv suele ser un enlace simbólico al Python
    del sistema y ambos resolverían a la misma ruta, provocando falsos positivos.
    """
    if not get_venv_dir().exists():
        return False
    return Path(sys.prefix).resolve() == get_venv_dir().resolve()


def create_venv() -> None:
    """Crea un entorno virtual nuevo."""
    venv_dir = get_venv_dir()
    venv_dir.parent.mkdir(parents=True, exist_ok=True)
    print(f"Creando entorno virtual en {venv_dir} …")
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv_dir)],
        check=True,
        cwd=PROJECT_DIR,
    )
    print("Entorno virtual creado.")


def ensure_venv() -> Path:
    """
    Garantiza que existe .venv y devuelve la ruta a su ejecutable Python.

    Si el entorno no existe, lo crea antes de devolver la ruta.
    """
    venv_python = get_venv_python()
    if not venv_python.exists():
        create_venv()
        venv_python = get_venv_python()
    if not venv_python.exists():
        raise RuntimeError("No se pudo crear el entorno virtual.")
    return venv_python


def install_dependencies(venv_python: Path) -> None:
    """
    Instala (o actualiza) las dependencias dentro del entorno virtual.

    Usa requirements.txt si existe; en caso contrario instala los paquetes
    mínimos definidos en REQUIRED_PACKAGES.
    """
    print("Instalando dependencias en el entorno virtual …")

    # Actualizar pip de forma silenciosa.
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "-q", "--upgrade", "pip"],
        check=True,
        cwd=PROJECT_DIR,
    )

    if REQUIREMENTS_FILE.exists():
        cmd = [
            str(venv_python),
            "-m",
            "pip",
            "install",
            "-q",
            "-r",
            str(REQUIREMENTS_FILE),
        ]
    else:
        cmd = [str(venv_python), "-m", "pip", "install", "-q", *REQUIRED_PACKAGES]

    subprocess.run(cmd, check=True, cwd=PROJECT_DIR)
    print("Dependencias instaladas correctamente.")


def launch_app() -> int:
    """
    Importa y arranca la interfaz gráfica de LEFA.

    Solo debe llamarse cuando ya estamos ejecutando con el Python del venv,
    de modo que PyQt6 y el resto de paquetes estén disponibles.
    """
    from main import main as lefa_main

    return lefa_main()


def main() -> int:
    """Orquesta la preparación del entorno y el arranque de la aplicación."""
    os.chdir(PROJECT_DIR)
    os.environ.setdefault("LEFA_PROJECT_DIR", str(PROJECT_DIR))
    if str(PROJECT_DIR) not in sys.path:
        sys.path.insert(0, str(PROJECT_DIR))

    if is_running_in_venv():
        try:
            return launch_app()
        except Exception as exc:
            import traceback

            print(f"Error al iniciar LEFA: {exc}", file=sys.stderr)
            traceback.print_exc()
            return 1

    try:
        venv_python = ensure_venv()
        install_dependencies(venv_python)

        print("Iniciando LEFA …")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_DIR)
        env["LEFA_PROJECT_DIR"] = str(PROJECT_DIR)
        os.environ.update(env)
        argv = [str(venv_python), str(__file__), *sys.argv[1:]]
        # Reemplaza este proceso por el Python del venv (sin proceso padre bloqueando
        # la terminal en subprocess.run tras cerrar la aplicación).
        os.execv(str(venv_python), argv)
        return 1

    except subprocess.CalledProcessError as exc:
        print(f"Error al preparar el entorno: {exc}", file=sys.stderr)
        print(
            "\nSugerencias:\n"
            "- Comprueba tu conexión a internet.\n"
            "- Instala manualmente: .venv/bin/pip install -r requirements.txt\n"
            "- Recrea el entorno: borra ~/.local/share/lefa/.venv "
            "(o .venv en el proyecto) y vuelve a ejecutar.",
            file=sys.stderr,
        )
        return 1
    except KeyboardInterrupt:
        print("\nAplicación cerrada por el usuario.")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
