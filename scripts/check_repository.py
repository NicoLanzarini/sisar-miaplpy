import os
import json
from pathlib import Path


def check_local_repository(repo_path: str, dates: list, bbox: list) -> dict:
    """
    Verifica si las imagenes SLC ya estan en el repositorio local.
    Retorna cuales fechas estan disponibles y cuales faltan.
    """
    repo = Path(repo_path)
    available = []
    missing = []

    if not repo.exists():
        print(f"Repositorio local no encontrado: {repo_path}")
        return {"available": [], "missing": dates}

    for date in dates:
        slc_files = list(repo.glob(f"*{date}*.zip")) + list(repo.glob(f"*{date}*.SAFE"))
        if slc_files:
            available.append(date)
            print(f"[OK] {date} encontrada en repositorio local")
        else:
            missing.append(date)
            print(f"[--] {date} no encontrada, se descargara de Vertex")

    return {"available": available, "missing": missing}


if __name__ == "__main__":
    import sys

    config_path = sys.argv[1] if len(sys.argv) > 1 else "/workspace/config.json"

    with open(config_path) as f:
        config = json.load(f)

    result = check_local_repository(
        repo_path=config["repository_path"],
        dates=config["dates"],
        bbox=config["bbox"]
    )

    print(json.dumps(result, indent=2))
