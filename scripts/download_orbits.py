import os
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta


# Nuevo servidor de orbitas ESA (reemplazo de scihub desde 2023)
ESA_ORBIT_URL = "https://step.esa.int/auxdata/orbits/Sentinel-1"


def download_orbits(dates: list, output_dir: str):
    """
    Descarga orbitas precisas (POEORB) de Sentinel-1 desde ESA step.esa.int
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    for date in dates:
        dt = datetime.strptime(date, "%Y%m%d")
        year = dt.strftime("%Y")
        month = dt.strftime("%m")

        existing = list(output.glob(f"*POEORB*{date}*"))
        if existing:
            print(f"[OK] Orbita para {date} ya existe.")
            continue

        print(f"Descargando orbita POEORB para {date}...")

        # URL del directorio de orbitas para ese mes
        dir_url = f"{ESA_ORBIT_URL}/POEORB/S1A/{year}/{month}/"

        try:
            response = requests.get(dir_url, timeout=30)
            if response.status_code != 200:
                print(f"[WARN] No se pudo acceder al directorio de orbitas para {date}")
                continue

            # Buscar el archivo que corresponde a la fecha
            lines = response.text.split('\n')
            orbit_file = None
            for line in lines:
                if f"_{date}" in line and "POEORB" in line and ".EOF" in line:
                    start = line.find('"') + 1
                    end = line.find('"', start)
                    orbit_file = line[start:end]
                    break

            if not orbit_file:
                print(f"[WARN] No se encontro orbita POEORB para {date}")
                continue

            download_url = f"{dir_url}{orbit_file}"
            print(f"  Descargando: {orbit_file}")

            r = requests.get(download_url, stream=True, timeout=60)
            save_path = output / orbit_file

            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"[OK] Orbita descargada: {orbit_file}")

        except Exception as e:
            print(f"[WARN] Error descargando orbita para {date}: {e}")
            continue

    print("Descarga de orbitas completada.")


if __name__ == "__main__":
    import sys

    config_path = sys.argv[1] if len(sys.argv) > 1 else "/workspace/config.json"

    with open(config_path) as f:
        config = json.load(f)

    download_orbits(
        dates=config["dates"],
        output_dir=config["orbits_dir"]
    )
