import os
import json
import asf_search as asf
from pathlib import Path


def download_slc(dates: list, bbox: list, output_dir: str, max_scenes: int = None):
    """
    Descarga imagenes SLC de Sentinel-1 desde ASF Vertex.
    bbox: [sur, norte, oeste, este]
    max_scenes: limita la cantidad de escenas a descargar (util para tests)
    """
    user = os.environ.get("EARTHDATA_USER")
    password = os.environ.get("EARTHDATA_PASS")

    if not user or not password:
        raise ValueError("Faltan credenciales EARTHDATA_USER y EARTHDATA_PASS")

    session = asf.ASFSession().auth_with_creds(user, password)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    sur, norte, oeste, este = bbox
    wkt = f"POLYGON(({oeste} {sur},{este} {sur},{este} {norte},{oeste} {norte},{oeste} {sur}))"

    if max_scenes:
        dates = dates[:max_scenes]
        print(f"[TEST] Modo test: descargando solo {max_scenes} escena(s)")

    for date in dates:
        print(f"\nBuscando imagen para fecha: {date}")

        # asf_search requiere formato YYYY-MM-DD
        date_fmt = f"{date[:4]}-{date[4:6]}-{date[6:8]}"

        results = asf.search(
            platform=asf.PLATFORM.SENTINEL1,
            processingLevel=asf.PRODUCT_TYPE.SLC,
            beamMode=asf.BEAMMODE.IW,
            intersectsWith=wkt,
            start=f"{date_fmt}T00:00:00Z",
            end=f"{date_fmt}T23:59:59Z",
            maxResults=1
        )

        if not results:
            print(f"[WARN] No se encontraron imagenes para {date}")
            continue

        scene = results[0]
        print(f"[OK] Encontrada: {scene.properties['fileName']}")
        print(f"     Tamanio: {scene.properties.get('bytes', 'desconocido')} bytes")
        print(f"     Descargando en {output}...")

        results.download(path=str(output), session=session)
        print(f"[OK] Descarga completada para {date}")

    print("\nDescarga finalizada.")


if __name__ == "__main__":
    import sys

    config_path = sys.argv[1] if len(sys.argv) > 1 else "/workspace/config.json"
    missing_dates = sys.argv[2].split(",") if len(sys.argv) > 2 else []
    max_scenes = int(sys.argv[3]) if len(sys.argv) > 3 else None

    with open(config_path) as f:
        config = json.load(f)

    download_slc(
        dates=missing_dates or config["dates"],
        bbox=config["bbox"],
        output_dir=config["slc_dir"],
        max_scenes=max_scenes
    )
