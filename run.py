import os
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
VENV_DIR = BASE_DIR / ".venv"
VENV_PYTHON = VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
REQUIREMENTS = BASE_DIR / "requirements.txt"
INSTALL_STAMP = VENV_DIR / ".requirements-installed"


def in_project_venv():
    return Path(sys.executable).resolve() == VENV_PYTHON.resolve()


def requirements_need_install():
    if not INSTALL_STAMP.exists():
        return True
    return REQUIREMENTS.stat().st_mtime > INSTALL_STAMP.stat().st_mtime


def bootstrap_venv():
    if not VENV_PYTHON.exists():
        print("Creating virtual environment in .venv ...")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])
    if requirements_need_install():
        print("Installing project dependencies ...")
        env = os.environ.copy()
        env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
        subprocess.check_call([str(VENV_PYTHON), "-m", "pip", "install", "-r", str(REQUIREMENTS)], env=env)
        INSTALL_STAMP.touch()
    if not in_project_venv():
        os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(__file__), *sys.argv[1:]])


bootstrap_venv()

from app import create_app
from app.extensions import db

app = create_app()


@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database initialized.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        from app.models import LearningItem

        if LearningItem.query.count() == 0:
            from seed import seed

            seed()
            print("Starter content loaded.")
    app.run(debug=True)
