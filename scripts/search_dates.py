"""
Busca fechas disponibles de Sentinel-1 en ASF Vertex para una region dada.
Lee los parametros de config.json (bbox y rango de fechas).

Uso:
  python search_dates.py                          # usa /workspace/config.json
  python search_dates.py /ruta/a/config.json      # config personalizado
"""

import sys
import json
import asf_search as asf


def search_dates(bbox: list, start_date: str, end_date: str, max_results: int = 50):
    """
    Busca imagenes Sentinel-1 SLC disponibles en ASF Vertex.
    bbox: [sur, norte, oeste, este]
    start_date, end_date: formato YYYYMMDD
    """
    sur, norte, oeste, este = bbox
    wkt = f"POLYGON(({oeste} {sur},{este} {sur},{este} {norte},{oeste} {norte},{oeste} {sur}))"

    # Formatear fechas YYYYMMDD -> YYYY-MM-DDT00:00:00Z
    start_fmt = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:8]}T00:00:00Z"
    end_fmt = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]}T23:59:59Z"

    print(f"Buscando imagenes Sentinel-1 SLC...")
    print(f"  Region: {bbox}")
    print(f"  Periodo: {start_date} a {end_date}")
    print()

    results = asf.search(
        platform=asf.PLATFORM.SENTINEL1,
        processingLevel=asf.PRODUCT_TYPE.SLC,
        beamMode=asf.BEAMMODE.IW,
        intersectsWith=wkt,
        start=start_fmt,
        end=end_fmt,
        maxResults=max_results
    )

    if not results:
        print("No se encontraron imagenes para ese periodo y region.")
        return []

    print(f"Se encontraron {len(results)} imagenes:")
    dates_found = []
    for r in results:
        date_str = r.properties['startTime'][:10]
        filename = r.properties['fileName']
        print(f"  {date_str}  {filename}")
        dates_found.append(date_str.replace("-", ""))

    return dates_found


if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else "/workspace/config.json"

    with open(config_path) as f:
        config = json.load(f)

    bbox = config["bbox"]
    dates = config.get("dates", [])

    # Usar primera y ultima fecha del config, o un rango por defecto
    if len(dates) >= 2:
        start_date = dates[0]
        end_date = dates[-1]
    else:
        start_date = config.get("search_start", "20230101")
        end_date = config.get("search_end", "20230201")

    search_dates(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        max_results=config.get("max_search_results", 50)
    )
