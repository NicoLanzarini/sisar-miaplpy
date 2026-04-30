#!/bin/bash
# SISAR - MiaplPy Pipeline (Docker)
# CEDIAC - UNCuyo / CONICET
# Uso: bash run.sh /ruta/a/datos

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================"
echo " SISAR - MiaplPy Pipeline (Docker)"
echo " CEDIAC - UNCuyo / CONICET"
echo "============================================"
echo ""

# ── 1. Verificar Docker ───────────────────────────────────────────────────────
if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker no está corriendo."
    echo "        En Linux: sudo systemctl start docker"
    echo "        En Mac: abrí Docker Desktop"
    exit 1
fi
echo "[OK] Docker está corriendo."

# ── 2. Verificar .env ─────────────────────────────────────────────────────────
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo ""
    echo "[ERROR] No se encontró .env en $SCRIPT_DIR"
    echo ""
    echo "        Crealo con:"
    echo "          echo 'EARTHDATA_USER=tu_usuario' > .env"
    echo "          echo 'EARTHDATA_PASS=tu_clave'   >> .env"
    exit 1
fi
echo "[OK] Credenciales encontradas."

# ── 3. Directorio de datos ────────────────────────────────────────────────────
if [ -n "$1" ]; then
    DATA_DIR="$1"
else
    echo ""
    echo "Donde están (o se guardarán) los datos?"
    echo "Ejemplo: /data/sisar  o  /home/usuario/datos"
    echo ""
    read -r -p "Directorio de datos: " DATA_DIR
fi

mkdir -p "$DATA_DIR"/{slc,dem,orbits,isce2_output,series_ps,output}
echo "[OK] Directorio de datos: $DATA_DIR"

# ── 4. Construir imagen si no existe ─────────────────────────────────────────
echo ""
if ! docker image inspect sisar-execute:latest > /dev/null 2>&1; then
    echo "[BUILD] Construyendo imagen sisar-execute:latest (15-60 min la primera vez)..."
    docker build -t sisar-execute:latest "$SCRIPT_DIR"
    echo "[OK] Imagen construida."
else
    echo "[OK] Imagen sisar-execute:latest ya existe."
fi

# ── 5. Correr pipeline ────────────────────────────────────────────────────────
echo ""
echo "============================================"
echo " Iniciando pipeline..."
echo " Datos en: $DATA_DIR"
echo "============================================"
echo ""

docker run --rm \
  --env-file "$SCRIPT_DIR/.env" \
  -v "$SCRIPT_DIR/config.json:/workspace/config.json" \
  -v "$DATA_DIR/slc:/workspace/slc" \
  -v "$DATA_DIR/dem:/workspace/dem" \
  -v "$DATA_DIR/orbits:/workspace/orbits" \
  -v "$DATA_DIR/isce2_output:/workspace/isce2_output" \
  -v "$DATA_DIR/series_ps:/workspace/series_ps" \
  -v "$DATA_DIR/output:/workspace/output" \
  sisar-execute:latest

echo ""
echo "============================================"
echo " Pipeline finalizado."
echo " Resultados en: $DATA_DIR/series_ps"
echo "============================================"
