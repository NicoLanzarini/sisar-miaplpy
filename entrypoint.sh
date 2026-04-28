#!/bin/bash
set -e

CONFIG=/workspace/config.json
SCRIPTS=/workspace/scripts

echo "============================================"
echo " SISAR - Ejecutor MiaplPy"
echo " Job: $(python -c "import json; print(json.load(open('$CONFIG'))['job_id'])")"
echo "============================================"

# 1. Verificar repositorio local
echo ""
echo "[1/5] Verificando repositorio local..."
MISSING=$(python $SCRIPTS/check_repository.py $CONFIG | python -c "
import sys, json
data = json.load(sys.stdin)
print(','.join(data['missing']))
")

# 2. Descargar imagenes faltantes de Vertex
if [ -n "$MISSING" ]; then
    echo ""
    echo "[2/5] Descargando imagenes faltantes de Vertex ASF..."
    echo "      Fechas: $MISSING"
    python $SCRIPTS/download_asf.py $CONFIG $MISSING
else
    echo ""
    echo "[2/5] Todas las imagenes disponibles en repositorio local."
fi

# 3. Descargar DEM y orbitas
echo ""
echo "[3/5] Descargando DEM y orbitas..."
python $SCRIPTS/download_dem.py $CONFIG
python $SCRIPTS/download_orbits.py $CONFIG

# 4. Correr ISCE2 topsStack
echo ""
echo "[4/5] Ejecutando ISCE2 topsStack..."
python $SCRIPTS/run_isce2.py $CONFIG

# 5. Correr MiaplPy
echo ""
echo "[5/5] Ejecutando MiaplPy..."
python $SCRIPTS/run_miaplpy.py $CONFIG

echo ""
echo "============================================"
echo " Procesamiento finalizado exitosamente."
echo "============================================"
