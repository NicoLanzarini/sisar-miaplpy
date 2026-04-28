# SISAR — Ejecutor MiaplPy en Docker

Pipeline de procesamiento InSAR con MiaplPy containerizado en Docker.
Desarrollado para el proyecto SISAR (CEDIAC-UNCUYO / CONICET).

---

## Descripción

Este módulo implementa el **Agente de Procesamiento** del sistema SISAR,
específicamente el workflow **ISCE2 + MiaplPy** para generación de series
temporales de deformación a partir de imágenes Sentinel-1.

El pipeline completo hace:
1. Verifica si las imágenes SLC ya están en el repositorio local
2. Descarga las imágenes faltantes desde ASF Vertex (NASA)
3. Descarga el DEM de Copernicus (30m) y las órbitas precisas (ESA)
4. Corre ISCE2 topsStack para corregistrar las imágenes
5. Corre MiaplPy para generar la serie temporal de deformación

---

## Requisitos

- Docker Desktop instalado y corriendo
- Cuenta en [NASA Earthdata](https://urs.earthdata.nasa.gov) (gratuita)
- ~500 GB de disco disponible para datos reales
- 16 GB RAM mínimo para correr ISCE2

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/sisar-miaplpy.git
cd sisar-miaplpy
```

### 2. Crear el archivo de credenciales

```bash
# Crear .env con las credenciales de NASA Earthdata
echo "EARTHDATA_USER=tu_usuario" > .env
echo "EARTHDATA_PASS=tu_password" >> .env
```

> **IMPORTANTE**: El archivo `.env` nunca debe subirse a GitHub.
> Ya está incluido en el `.gitignore`.

### 3. Construir la imagen Docker

```bash
docker build -t miaplpy:1.0 .
```

El build tarda aproximadamente 15-60 minutos dependiendo
de la velocidad de internet. Instala ISCE2, MiaplPy, MintPy
y todas las dependencias automáticamente.

---

## Configuración

Editá el archivo `config.json` con los parámetros de tu trabajo:

```json
{
    "job_id": "nombre_del_trabajo",
    "bbox": [sur, norte, oeste, este],
    "dates": ["20230109", "20230121", "..."],
    "phase_linking_method": "EMI",
    "azimuth_looks": 5,
    "range_looks": 20
}
```

### Parámetros principales

| Parámetro | Descripción | Valores posibles |
|---|---|---|
| `bbox` | Bounding box [S, N, O, E] | coordenadas decimales |
| `dates` | Fechas a procesar | formato YYYYMMDD |
| `phase_linking_method` | Algoritmo de phase linking | EMI, EVD, PTA |
| `azimuth_looks` | Looks en azimuth | 5 (default) |
| `range_looks` | Looks en rango | 20 (default) |

---

## Uso

### Correr el pipeline completo

```bash
docker run --rm \
  --env-file .env \
  -v $(pwd)/config.json:/workspace/config.json \
  -v /ruta/a/datos:/workspace \
  miaplpy:1.0
```

### Correr scripts individuales

```bash
# Buscar fechas disponibles para una región
docker run --rm --env-file .env miaplpy:1.0 \
  python /workspace/scripts/search_dates.py

# Solo descargar imágenes (modo test: 1 escena)
docker run --rm --env-file .env \
  -v $(pwd)/config.json:/workspace/config.json \
  -v /ruta/datos:/workspace/slc \
  miaplpy:1.0 python /workspace/scripts/download_asf.py \
  /workspace/config.json 20230109 1

# Solo descargar DEM
docker run --rm \
  -v $(pwd)/config.json:/workspace/config.json \
  -v /ruta/datos:/workspace/dem \
  miaplpy:1.0 python /workspace/scripts/download_dem.py \
  /workspace/config.json
```

---

## Estructura del proyecto

```
docker/
├── Dockerfile              # Define la imagen Docker
├── environment.yml         # Paquetes conda/pip
├── docker-compose.yml      # Orquesta contenedores
├── .env                    # Credenciales (NO subir a git)
├── .gitignore              # Archivos excluidos de git
├── config.json             # Parámetros del trabajo
├── entrypoint.sh           # Script principal del pipeline
└── scripts/
    ├── check_repository.py    # Verifica repo local
    ├── search_dates.py        # Busca fechas en ASF Vertex
    ├── download_asf.py        # Descarga SLCs de NASA/ASF
    ├── download_dem.py        # Descarga DEM Copernicus
    ├── download_orbits.py     # Descarga órbitas ESA
    ├── run_isce2.py           # Ejecuta ISCE2 topsStack
    └── run_miaplpy.py         # Ejecuta MiaplPy
```

---

## Estructura de datos esperada

```
workspace/
├── slc/            # Imágenes SLC de Sentinel-1 (.zip)
├── dem/            # DEM Copernicus (dem.tif)
├── orbits/         # Órbitas POEORB (.EOF)
├── isce2_output/   # Outputs de ISCE2 (generados por ISCE2 Docker)
│   ├── merged/
│   │   ├── SLC/*/*.slc.full
│   │   └── geom_reference/hgt.rdr.full ...
│   ├── baselines/
│   └── reference/IW*.xml
└── series_ps/      # Outputs de MiaplPy (generados por este Docker)
```

---

## Stack tecnológico

| Herramienta | Versión | Función |
|---|---|---|
| ISCE2 | conda-forge | Corregistro de SLCs |
| MiaplPy | insarlab/MiaplPy | Series temporales (Phase Linking) |
| MintPy | conda-forge | Corrección atmosférica y resultados |
| sardem | pip | Descarga DEM Copernicus |
| asf_search | pip | Búsqueda y descarga desde ASF Vertex |
| snaphu | conda-forge | Unwrapping de fase |

---

## Estado del desarrollo

- [x] Docker build completo
- [x] Descarga de SLCs desde ASF Vertex
- [x] Descarga de DEM Copernicus
- [x] Descarga de órbitas ESA POEORB
- [x] Template de MiaplPy generado automáticamente
- [ ] Prueba con outputs reales de ISCE2
- [ ] Script de resultados (velocity.jpg, timeseries.csv)
- [ ] Integración con servidor SISAR

---

## Próximos pasos

1. Conseguir outputs reales de ISCE2 para probar MiaplPy
2. Ajustar paths según estructura real de ISCE2
3. Agregar script de generación de resultados
4. Integrar con el sistema SISAR completo

---

## Autores

Desarrollado en el marco del proyecto SISAR
CEDIAC — Universidad Nacional de Cuyo / CONICET
