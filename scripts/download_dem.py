import os
import json
import subprocess
from pathlib import Path


def download_dem(bbox: list, output_dir: str):
    """
    Descarga DEM de Copernicus 30m usando sardem.
    bbox: [sur, norte, oeste, este]
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    dem_file = output / "dem.tif"
    if dem_file.exists():
        print(f"[OK] DEM ya existe en {dem_file}, omitiendo descarga.")
        return str(dem_file)

    sur, norte, oeste, este = bbox
    print(f"Descargando DEM Copernicus para bbox: {sur} {norte} {oeste} {este}")

    cmd = [
        "sardem",
        "--bbox", str(oeste), str(sur), str(este), str(norte),
        "--output", str(dem_file),
        "--data", "COP"
    ]

    subprocess.run(cmd, check=True, cwd=str(output))
    print(f"[OK] DEM descargado en {dem_file}")
    return str(dem_file)


if __name__ == "__main__":
    import sys

    config_path = sys.argv[1] if len(sys.argv) > 1 else "/workspace/config.json"

    with open(config_path) as f:
        config = json.load(f)

    download_dem(
        bbox=config["bbox"],
        output_dir=config["dem_dir"]
    )
