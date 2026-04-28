import os
import json
import subprocess
from pathlib import Path


def generate_template(config: dict, work_dir: Path) -> Path:
    """
    Genera el archivo de configuracion de MiaplPy
    siguiendo exactamente la estructura del equipo CEDIAC-UNCUYO.
    """
    home = config.get("isce2_output", "/workspace/isce2_output")
    dir_miaplpy = str(work_dir)
    method = config.get("phase_linking_method", "EMI")

    bbox = config.get("bbox", [])
    mp_south, mp_north, mp_west, mp_east = bbox if bbox else ["", "", "", ""]

    ref_lat = config.get("ref_lat", "")
    ref_lon = config.get("ref_lon", "")

    lines = []

    # Processor
    lines.append("miaplpy.load.processor      = isce")
    lines.append("miaplpy.load.updateMode     = auto")
    lines.append("miaplpy.load.compression    = auto")
    lines.append("miaplpy.load.autoPath       = yes")

    # SLCs (con .full — estructura topsStack)
    lines.append(f"miaplpy.load.slcFile        = {home}/merged/SLC/*/*.slc.full")
    lines.append(f"miaplpy.load.metaFile       = {home}/reference/IW*.xml")
    lines.append(f"miaplpy.load.baselineDir    = {home}/baselines")

    # Geometria (con .full)
    lines.append(f"miaplpy.load.demFile          = {home}/merged/geom_reference/hgt.rdr.full")
    lines.append(f"miaplpy.load.lookupYFile      = {home}/merged/geom_reference/lat.rdr.full")
    lines.append(f"miaplpy.load.lookupXFile      = {home}/merged/geom_reference/lon.rdr.full")
    lines.append(f"miaplpy.load.incAngleFile     = {home}/merged/geom_reference/los.rdr.full")
    lines.append(f"miaplpy.load.azAngleFile      = {home}/merged/geom_reference/los.rdr.full")
    lines.append(f"miaplpy.load.shadowMaskFile   = {home}/merged/geom_reference/shadowMask.rdr.full")
    lines.append("miaplpy.load.waterMaskFile    = None")

    # Interferogramas (generados por MiaplPy, no por ISCE2)
    lines.append(f"miaplpy.load.unwFile        = {dir_miaplpy}/miaplpy/inverted/interferograms_single_reference/*/*fine.unw")
    lines.append(f"miaplpy.load.corFile        = {dir_miaplpy}/miaplpy/inverted/interferograms_single_reference/*/*fine.cor")
    lines.append(f"miaplpy.load.connCompFile   = {dir_miaplpy}/miaplpy/inverted/interferograms_single_reference/*/*.unw.conncomp")

    # Subset (bbox)
    if mp_south and mp_north and mp_west and mp_east:
        lines.append(f"miaplpy.subset.lalo = {mp_south}:{mp_north},{mp_west}:{mp_east}")
    else:
        lines.append("miaplpy.subset.lalo = auto")

    # Opciones MiaplPy
    lines.append("miaplpy.multiprocessing.numProcessor   = 2")
    lines.append("miaplpy.interferograms.type = single_reference")

    # Opciones MintPy integradas
    lines.append("mintpy.compute.cluster     = no")
    lines.append("mintpy.compute.numWorker   = 2")

    if ref_lat and ref_lon:
        lines.append(f"mintpy.reference.lalo = {ref_lat},{ref_lon}")
    else:
        lines.append("mintpy.reference.lalo = auto")

    lines.append("mintpy.troposphericDelay.method = no")

    template_content = "\n".join(lines)
    template_path = work_dir / "parametros_miaplpy.txt"
    template_path.write_text(template_content)

    print(f"[OK] Template generado: {template_path}")
    return template_path


def verify_isce2_outputs(home: str) -> bool:
    """Verifica que los outputs de ISCE2 necesarios existen."""
    required = [
        f"{home}/merged/SLC",
        f"{home}/merged/geom_reference/hgt.rdr.full",
        f"{home}/merged/geom_reference/lat.rdr.full",
        f"{home}/merged/geom_reference/lon.rdr.full",
        f"{home}/merged/geom_reference/los.rdr.full",
        f"{home}/baselines",
        f"{home}/reference",
    ]

    all_ok = True
    for path in required:
        if Path(path).exists():
            print(f"[OK] {path}")
        else:
            print(f"[!!] No encontrado: {path}")
            all_ok = False

    return all_ok


def run_miaplpy(config: dict):
    """Corre el pipeline completo de MiaplPy."""
    home = config.get("isce2_output", "/workspace/isce2_output")
    work_dir = Path(config.get("miaplpy_output", "/workspace/series_ps"))
    work_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("Verificando outputs de ISCE2...")
    print("=" * 50)

    if not verify_isce2_outputs(home):
        raise FileNotFoundError(
            "Faltan outputs de ISCE2. "
            "Asegurate de correr ISCE2 antes de MiaplPy."
        )

    print("")
    print("=" * 50)
    print("Generando template de MiaplPy...")
    print("=" * 50)

    template_path = generate_template(config, work_dir)

    print("")
    print("=" * 50)
    print(f"Corriendo MiaplPy...")
    print(f"Metodo: {config.get('phase_linking_method', 'EMI')}")
    print(f"Directorio: {work_dir}")
    print("=" * 50)

    cmd = [
        "miaplpyApp.py",
        str(template_path),
        "--dir", str(work_dir)
    ]

    subprocess.run(cmd, check=True, cwd=str(work_dir))

    print("")
    print("[OK] MiaplPy completado exitosamente.")
    print(f"Resultados en: {work_dir}")


if __name__ == "__main__":
    import sys

    config_path = sys.argv[1] if len(sys.argv) > 1 else "/workspace/config.json"

    with open(config_path) as f:
        config = json.load(f)

    run_miaplpy(config)
