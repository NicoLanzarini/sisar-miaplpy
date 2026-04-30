# SISAR — Ejecutor MiaplPy en Docker

Pipeline de procesamiento InSAR con MiaplPy containerizado en Docker.
Desarrollado para el proyecto SISAR (CEDIAC-UNCUYO / CONICET).

---

## Descripcion

Este modulo implementa el **Agente de Procesamiento** del sistema SISAR,
especificamente el workflow **ISCE2 + MiaplPy** para generacion de series
temporales de deformacion a partir de imagenes Sentinel-1.

El pipeline completo realiza:
1. Verifica si las imagenes SLC ya estan en el repositorio local
2. Descarga las imagenes faltantes desde ASF Vertex (NASA)
3. Descarga el DEM de Copernicus (30m) y las orbitas precisas (ESA)
4. Corre ISCE2 topsStack para corregistrar las imagenes
5. Corre MiaplPy para generar la serie temporal de deformacion

---

## Que es MiaplPy y que hace?

MiaplPy (**MI**ami **A**mi **PL**inking in **PY**thon) es una herramienta de
procesamiento InSAR basada en **Phase Linking**, un algoritmo estadistico que
mejora la estimacion de fase usando todas las imagenes del stack en conjunto.

### Phase Linking — Algoritmos disponibles

| Algoritmo | Descripcion | Uso recomendado |
|---|---|---|
| **EMI** | Eigenvalue Minimization of Interferograms | Produccion (mas preciso) |
| **EVD** | Eigenvalue Decomposition | Casos simples |
| **PTA** | Phase Triangle Algorithm | Pruebas rapidas |

### Que es LOS?

**LOS (Line Of Sight)** es la direccion en la que el satelite mira hacia la
tierra (~38 grados de inclinacion). La deformacion se mide en esa direccion, no
verticalmente:

```
        Satelite
           /
          /  <- LOS (~38 grados)
         /
        /
    Suelo
```

- **LOS negativo** -> el suelo se aleja del satelite -> generalmente subsidencia
- **LOS positivo** -> el suelo se acerca al satelite -> generalmente levantamiento

### MiaplPy corrige errores?

**No.** MiaplPy no es un corrector, es un **estimador de fase mas robusto**:

| | InSAR clasico | MiaplPy |
|---|---|---|
| Pixeles usados | Solo PS (edificios, rocas) | PS + DS (vegetacion, suelo) |
| Zonas cubiertas | Urbanas | Urbanas + rurales + agricolas |
| Ruido de fase | Mayor | Menor (estadisticamente) |
| Correccion atmosferica | No | No (la hace MintPy despues) |

Las correcciones atmosfericas y de DEM las realiza **MintPy** en el paso siguiente.

### Por que la montana tiene pocos o ningun punto?

La coherencia en zonas montanosas es baja o nula por razones fisicas reales:
- **Vegetacion densa** -> la senal rebota diferente en cada pasada
- **Nieve y hielo** -> cambia la superficie completamente entre imagenes
- **Sombra y layover** -> el radar no llega o se superponen zonas
- **Pendientes fuertes** -> la geometria se distorsiona

MiaplPy mejora la situacion respecto al InSAR clasico, pero no puede recuperar
zonas donde directamente no hay senal coherente.

---

## Outputs del pipeline

El sistema genera tres productos principales:

| Producto | Formato | Descripcion |
|---|---|---|
| Mapa de velocidad | `.png` / `.jpg` | Velocidad de deformacion LOS en mm/anio |
| Serie temporal | `.png` + `.csv` | Deformacion acumulada por punto en el tiempo |
| Mapa de coherencia | `.png` | Calidad de la senal por pixel (0-1) |

---

## Ejemplos de resultados

> **ADVERTENCIA: Las siguientes imagenes son DATOS SINTETICOS generados
> con fines demostrativos. NO se han utilizado imagenes satelitales reales
> para esta demo. Los valores, patrones y zonas son completamente ficticios.**

### Mapa de Velocidad de Deformacion

![Mapa de Velocidad](example_outputs/velocity_map.png)

Cada punto representa un pixel PS (Persistent Scatterer) o DS (Distributed
Scatterer) detectado por MiaplPy. El color indica la velocidad de deformacion:
- **Azul** -> subsidencia (hundimiento)
- **Rojo** -> levantamiento
- **Zonas vacias** -> baja coherencia, sin datos confiables

### Serie Temporal de Deformacion

![Serie Temporal](example_outputs/timeseries.png)

Muestra la evolucion temporal de la deformacion en tres puntos representativos:
- **Punto A** -> zona de subsidencia maxima
- **Punto B** -> zona urbana estable
- **Punto C** -> zona de cultivos con senal estacional

La linea roja punteada indica la tendencia lineal (velocidad promedio).

### Mapa de Coherencia Temporal

![Coherencia](example_outputs/coherence_map.png)

Indica la calidad de la senal radar en cada punto. Valores altos (amarillo/verde)
indican pixeles confiables. MiaplPy descarta puntos con coherencia menor a 0.35.

---

## Requisitos

- Docker Desktop instalado y corriendo
- Cuenta en [NASA Earthdata](https://urs.earthdata.nasa.gov) (gratuita)
- ~500 GB de disco disponible para datos reales
- 16 GB RAM minimo para correr ISCE2

---

## Instalacion

### 1. Clonar el repositorio

```bash
git clone https://github.com/NicoLanzarini/sisar-miaplpy.git
cd sisar-miaplpy
```

### 2. Crear el archivo de credenciales

```bash
echo "EARTHDATA_USER=tu_usuario" > .env
echo "EARTHDATA_PASS=tu_password" >> .env
```

> **IMPORTANTE**: El archivo `.env` nunca debe subirse a GitHub.
> Ya esta incluido en el `.gitignore`.

### 3. Construir la imagen Docker

```bash
docker build -t sisar-execute:latest .
```

El build tarda aproximadamente 15-60 minutos. Instala ISCE2, MiaplPy, MintPy
y todas las dependencias automaticamente.

### 4. Crear la carpeta de datos

```bash
mkdir -p data/{slc,dem,orbits,isce2_output,series_ps,output}
```

---

## Configuracion

Editar el archivo `config.json` con los parametros del trabajo:

```json
{
    "job_id": "nombre_del_trabajo",
    "bbox": [-33.0, -31.0, -69.0, -67.0],
    "dates": ["20230109", "20230121"],
    "phase_linking_method": "EMI",
    "azimuth_looks": 5,
    "range_looks": 20
}
```

### Parametros principales

| Parametro | Descripcion | Valores posibles |
|---|---|---|
| `bbox` | Bounding box [S, N, O, E] | coordenadas decimales |
| `dates` | Fechas a procesar | formato YYYYMMDD |
| `phase_linking_method` | Algoritmo de phase linking | EMI, EVD, PTA |
| `azimuth_looks` | Looks en azimuth | 5 (default) |
| `range_looks` | Looks en rango | 20 (default) |

---

## Uso

### Opcion 1 — run.bat (Windows, mas facil)

Doble clic en `run.bat` o desde CMD:

```cmd
cd sisar-miaplpy
run.bat
```

Te pregunta donde estan los datos y corre el pipeline completo.

### Opcion 2 — run.sh (Linux/Mac)

```bash
# Con ruta como argumento
bash run.sh /ruta/a/datos

# O interactivo (te pregunta la ruta)
bash run.sh
```

### Opcion 3 — Docker Compose

```bash
docker compose up
```

Los datos deben estar en la carpeta `./data/` del proyecto.

### Opcion 4 — Docker Run manual

```bash
docker run --rm \
  --env-file .env \
  -v $(pwd)/config.json:/workspace/config.json \
  -v /ruta/datos/slc:/workspace/slc \
  -v /ruta/datos/dem:/workspace/dem \
  -v /ruta/datos/orbits:/workspace/orbits \
  -v /ruta/datos/isce2_output:/workspace/isce2_output \
  -v /ruta/datos/series_ps:/workspace/series_ps \
  -v /ruta/datos/output:/workspace/output \
  sisar-execute:latest
```

### Correr scripts individuales

```bash
# Buscar fechas disponibles para una region
docker run --rm --env-file .env \
  -v $(pwd)/config.json:/workspace/config.json \
  sisar-execute:latest python /workspace/scripts/search_dates.py

# Solo descargar imagenes (modo test: 1 escena)
docker run --rm --env-file .env \
  -v $(pwd)/config.json:/workspace/config.json \
  -v /ruta/datos/slc:/workspace/slc \
  sisar-execute:latest python /workspace/scripts/download_asf.py \
  /workspace/config.json 20230109 1

# Solo descargar DEM
docker run --rm \
  -v $(pwd)/config.json:/workspace/config.json \
  -v /ruta/datos/dem:/workspace/dem \
  sisar-execute:latest python /workspace/scripts/download_dem.py \
  /workspace/config.json

# Generar outputs de ejemplo (datos sinteticos)
docker run --rm \
  -v $(pwd)/example_outputs:/workspace/example_outputs \
  sisar-execute:latest bash -c "cd /workspace && python scripts/generate_example_outputs.py"
```

---

## Estructura del proyecto

```
sisar-miaplpy/
├── Dockerfile                      # Define la imagen Docker
├── environment.yml                 # Paquetes conda/pip
├── docker-compose.yml              # Orquesta contenedores
├── run.bat                         # Ejecuta pipeline en Windows
├── run.sh                          # Ejecuta pipeline en Linux/Mac
├── .env                            # Credenciales (NO subir a git)
├── .gitignore                      # Archivos excluidos de git
├── config.json                     # Parametros del trabajo
├── entrypoint.sh                   # Script principal del pipeline
├── data/                           # Datos de procesamiento (NO sube a git)
│   ├── slc/                        # Imagenes SLC Sentinel-1
│   ├── dem/                        # DEM Copernicus
│   ├── orbits/                     # Orbitas POEORB
│   ├── isce2_output/               # Outputs de ISCE2
│   ├── series_ps/                  # Outputs de MiaplPy
│   └── output/                     # Resultados finales
├── example_outputs/                # Imagenes de ejemplo (sinteticas)
│   ├── velocity_map.png
│   ├── timeseries.png
│   ├── coherence_map.png
│   └── timeseries.csv
└── scripts/
    ├── check_repository.py         # Verifica repo local
    ├── search_dates.py             # Busca fechas en ASF Vertex
    ├── download_asf.py             # Descarga SLCs de NASA/ASF
    ├── download_dem.py             # Descarga DEM Copernicus
    ├── download_orbits.py          # Descarga orbitas ESA
    ├── run_isce2.py                # Ejecuta ISCE2 topsStack
    ├── run_miaplpy.py              # Ejecuta MiaplPy
    └── generate_example_outputs.py # Genera demos sinteticas
```

---

## Estructura de datos esperada

```
data/
├── slc/            # Imagenes SLC de Sentinel-1 (.zip)
├── dem/            # DEM Copernicus (dem.tif)
├── orbits/         # Orbitas POEORB (.EOF)
├── isce2_output/   # Outputs de ISCE2
│   ├── merged/
│   │   ├── SLC/*/*.slc.full
│   │   └── geom_reference/hgt.rdr.full ...
│   ├── baselines/
│   └── reference/IW*.xml
└── series_ps/      # Outputs de MiaplPy
```

---

## Stack tecnologico

| Herramienta | Funcion |
|---|---|
| ISCE2 | Corregistro de SLCs (topsStack) |
| MiaplPy | Series temporales con Phase Linking |
| MintPy | Correccion atmosferica y resultados finales |
| sardem | Descarga DEM Copernicus |
| asf_search | Busqueda y descarga desde ASF Vertex |
| snaphu | Unwrapping de fase |

---

## Estado del desarrollo

- [x] Docker build completo
- [x] Descarga de SLCs desde ASF Vertex
- [x] Descarga de DEM Copernicus
- [x] Descarga de orbitas ESA POEORB
- [x] Template de MiaplPy generado automaticamente
- [x] Outputs de ejemplo generados
- [x] Scripts portables (sin rutas hardcodeadas)
- [x] run.bat (Windows) y run.sh (Linux/Mac)
- [ ] Prueba con outputs reales de ISCE2
- [ ] Script de resultados finales
- [ ] Integracion con servidor SISAR

---

## Proximos pasos

1. Conseguir outputs reales de ISCE2 para probar MiaplPy
2. Ajustar paths segun estructura real de ISCE2
3. Agregar script de generacion de resultados finales
4. Integrar con el sistema SISAR completo

---

## Autores

Desarrollado en el marco del proyecto SISAR
CEDIAC — Universidad Nacional de Cuyo / CONICET
