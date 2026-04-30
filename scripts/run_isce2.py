import os
import json
import subprocess
from pathlib import Path


def generate_topsstack_config(config: dict, work_dir: Path) -> str:
    """Genera el comando de stackSentinel.py con los parametros del job."""
    sur, norte, oeste, este = config["bbox"]
    bbox_str = f"{sur} {norte} {oeste} {este}"

    cmd = [
        "stackSentinel.py",
        "-s", config["slc_dir"],
        "-d", str(Path(config["dem_dir"]) / "dem.tif"),
        "-o", config["orbits_dir"],
        "-b", bbox_str,
        "-W", "interferogram",
        "-a", str(config.get("azimuth_looks", 5)),
        "-r", str(config.get("range_looks", 15)),
        "--text_cmd", "source /opt/conda/etc/profile.d/conda.sh && conda activate base &&"
    ]

    return cmd


def run_isce2(config: dict):
    """Corre el workflow topsStack de ISCE2."""
    work_dir = Path(config.get("isce2_output", "/workspace/isce2_output"))
    work_dir.mkdir(parents=True, exist_ok=True)

    print(f"Directorio de trabajo ISCE2: {work_dir}")

    # Generar steps de topsStack
    print("Generando pipeline topsStack...")
    cmd = generate_topsstack_config(config, work_dir)
    subprocess.run(cmd, check=True, cwd=str(work_dir))

    # Correr cada step generado
    run_files = sorted(work_dir.glob("run_files/run_*"))
    if not run_files:
        raise FileNotFoundError("No se generaron run_files. Verificar configuracion de ISCE2.")

    print(f"Encontrados {len(run_files)} steps para ejecutar.")

    for step in run_files:
        print(f"  Ejecutando: {step.name}")
        subprocess.run(["bash", str(step)], check=True, cwd=str(work_dir))

    print("[OK] ISCE2 topsStack completado.")
    return str(work_dir)


if __name__ == "__main__":
    import sys

    config_path = sys.argv[1] if len(sys.argv) > 1 else "/workspace/config.json"

    with open(config_path) as f:
        config = json.load(f)

    run_isce2(config)
