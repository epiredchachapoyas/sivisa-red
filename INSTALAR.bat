@echo off
setlocal EnableExtensions
title SIVISA - Instalacion de la publicacion automatica
cd /d "%~dp0"
set "RAIZ=%~dp0"
if "%RAIZ:~-1%"=="\" set "RAIZ=%RAIZ:~0,-1%"
echo.
echo  ============================================================
echo    SIVISA - Instalacion de la publicacion automatica
echo  ============================================================
echo   Carpeta del portal: %RAIZ%
echo   Se hace UNA sola vez en cada computadora. Tarda 5-10 minutos.
echo.

rem ---------- 1. Python ----------
set "PYDIR="
for /f "delims=" %%i in ('py -3 -c "import sys,os;print(os.path.dirname(sys.executable))" 2^>nul') do set "PYDIR=%%i"
if not defined PYDIR for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do set "PYDIR=%%D"
if not defined PYDIR (
  echo [1/5] Instalando Python...
  winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements
  for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do set "PYDIR=%%D"
)
if not exist "%PYDIR%\python.exe" (
  echo.
  echo  NO SE PUDO INSTALAR PYTHON. Instalelo desde https://www.python.org/downloads/
  echo  marcando "Add python.exe to PATH", y vuelva a abrir este archivo.
  pause & exit /b 1
)
echo [1/5] Python listo: %PYDIR%

rem ---------- 2. Git ----------
set "GIT="
for /f "delims=" %%i in ('where git 2^>nul') do if not defined GIT set "GIT=%%i"
if not defined GIT if exist "%ProgramFiles%\Git\cmd\git.exe" set "GIT=%ProgramFiles%\Git\cmd\git.exe"
if not defined GIT (
  echo [2/5] Instalando Git ^(puede pedir permiso de administrador: responda SI^)...
  winget install -e --id Git.Git --silent --accept-package-agreements --accept-source-agreements
  if exist "%ProgramFiles%\Git\cmd\git.exe" set "GIT=%ProgramFiles%\Git\cmd\git.exe"
)
if not defined GIT (
  echo.
  echo  NO SE PUDO INSTALAR GIT. Instalelo desde https://git-scm.com/download/win
  echo  ^(opciones por defecto^) y vuelva a abrir este archivo.
  pause & exit /b 1
)
echo [2/5] Git listo: %GIT%

rem ---------- 3. Paquetes de Python ----------
echo [3/5] Instalando paquetes (pandas, openpyxl, pillow)...
"%PYDIR%\python.exe" -m pip install --user --quiet --disable-pip-version-check pandas openpyxl pillow
if errorlevel 1 ( echo  No se pudieron instalar los paquetes. Revise la conexion a internet. & pause & exit /b 1 )

rem ---------- 4. Configuracion y primera publicacion ----------
"%GIT%" -C "%RAIZ%" config user.name "SIVISA automatico"
"%GIT%" -C "%RAIZ%" config user.email "epiredchachapoyas@users.noreply.github.com"
"%GIT%" -C "%RAIZ%" config credential.helper manager
if not exist "%RAIZ%\..\BASES_NOTISP\Maestros" (
  mkdir "%RAIZ%\..\BASES_NOTISP\Maestros" 2>nul
  echo  Se creo la carpeta BASES_NOTISP al lado del portal: copie alli la carpeta del anio y Maestros.
)
echo [4/5] Primera actualizacion. Si se abre una ventana de GitHub, inicie sesion
echo       con la cuenta epiredchachapoyas y pulse "Authorize" ^(solo esta vez^).
"%PYDIR%\python.exe" "%RAIZ%\herramientas\actualizar.py" --forzar

rem ---------- 5. Tarea automatica ----------
echo [5/5] Programando la tarea automatica...
powershell -NoProfile -ExecutionPolicy Bypass -File "%RAIZ%\herramientas\programar_tarea.ps1" -Pythonw "%PYDIR%\pythonw.exe" -Raiz "%RAIZ%"
echo.
echo  ============================================================
echo   LISTO. Desde ahora, cada 30 minutos (con la PC encendida):
echo    - si hay bases nuevas en BASES_NOTISP, se procesan solas;
echo    - todo lo nuevo en la carpeta del portal se publica solo.
echo   Registro: BASES_NOTISP\ULTIMA_ACTUALIZACION.txt
echo  ============================================================
pause
