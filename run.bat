@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

echo ============================================
echo  SISAR - MiaplPy Pipeline (Docker)
echo  CEDIAC - UNCuyo / CONICET
echo ============================================
echo.

:: ── 1. Verificar que Docker está corriendo ───────────────────────────────────
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker no está corriendo.
    echo         Abrí Docker Desktop y esperá a que termine de iniciar.
    echo.
    pause
    exit /b 1
)
echo [OK] Docker está corriendo.

:: ── 2. Verificar que existe .env ─────────────────────────────────────────────
if not exist "%~dp0.env" (
    echo.
    echo [ERROR] No se encontró el archivo .env con credenciales.
    echo.
    echo         Crealo en esta carpeta con el contenido:
    echo           EARTHDATA_USER=tu_usuario_nasa
    echo           EARTHDATA_PASS=tu_contraseña_nasa
    echo.
    pause
    exit /b 1
)
echo [OK] Credenciales encontradas.

:: ── 3. Preguntar directorio de datos ─────────────────────────────────────────
echo.
echo Donde están (o se guardarán) los datos de procesamiento?
echo Ejemplo: C:\datos\sisar  o  D:\SLC_Mendoza
echo.
echo IMPORTANTE: Se crearán las carpetas slc, dem, orbits, isce2_output, series_ps
echo             dentro de este directorio.
echo.
set /p DATA_DIR="Directorio de datos: "

:: Quitar comillas si las pusieron
set DATA_DIR=%DATA_DIR:"=%

:: Verificar que el directorio existe o crearlo
if not exist "%DATA_DIR%" (
    echo.
    echo El directorio no existe. Creando: %DATA_DIR%
    mkdir "%DATA_DIR%" 2>nul
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el directorio. Verificá la ruta.
        pause
        exit /b 1
    )
)
echo [OK] Directorio de datos: %DATA_DIR%

:: ── 4. Crear subcarpetas si no existen ───────────────────────────────────────
if not exist "%DATA_DIR%\slc"           mkdir "%DATA_DIR%\slc"
if not exist "%DATA_DIR%\dem"           mkdir "%DATA_DIR%\dem"
if not exist "%DATA_DIR%\orbits"        mkdir "%DATA_DIR%\orbits"
if not exist "%DATA_DIR%\isce2_output"  mkdir "%DATA_DIR%\isce2_output"
if not exist "%DATA_DIR%\series_ps"     mkdir "%DATA_DIR%\series_ps"
if not exist "%DATA_DIR%\output"        mkdir "%DATA_DIR%\output"

:: ── 5. Construir imagen si no existe ─────────────────────────────────────────
echo.
docker image inspect miaplpy:1.0 >nul 2>&1
if errorlevel 1 (
    echo [BUILD] Imagen miaplpy:1.0 no encontrada. Construyendo...
    echo         Esto puede tardar 15-60 minutos la primera vez.
    echo.
    docker build -t miaplpy:1.0 "%~dp0"
    if errorlevel 1 (
        echo.
        echo [ERROR] Falló la construcción de la imagen Docker.
        pause
        exit /b 1
    )
    echo [OK] Imagen construida exitosamente.
) else (
    echo [OK] Imagen miaplpy:1.0 ya existe.
)

:: ── 6. Correr el pipeline ─────────────────────────────────────────────────────
echo.
echo ============================================
echo  Iniciando pipeline de procesamiento...
echo  Datos en: %DATA_DIR%
echo ============================================
echo.

docker run --rm ^
  --env-file "%~dp0.env" ^
  -v "%~dp0config.json:/workspace/config.json" ^
  -v "%DATA_DIR%\slc:/workspace/slc" ^
  -v "%DATA_DIR%\dem:/workspace/dem" ^
  -v "%DATA_DIR%\orbits:/workspace/orbits" ^
  -v "%DATA_DIR%\isce2_output:/workspace/isce2_output" ^
  -v "%DATA_DIR%\series_ps:/workspace/series_ps" ^
  -v "%DATA_DIR%\output:/workspace/output" ^
  miaplpy:1.0

if errorlevel 1 (
    echo.
    echo [ERROR] El pipeline terminó con errores. Revisá los mensajes de arriba.
) else (
    echo.
    echo ============================================
    echo  Pipeline finalizado. Resultados en:
    echo  %DATA_DIR%\series_ps
    echo ============================================
)

echo.
pause
