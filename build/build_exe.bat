@echo off
echo ============================================
echo  VRain EXE Builder
echo ============================================

set PYINST=..\venv_build\Scripts\pyinstaller.exe

cd /d "%~dp0"

if not exist "%PYINST%" (
    echo ERROR: venv_build not found.
    echo Run from repo root:
    echo   python -m venv venv_build
    echo   venv_build\Scripts\pip install -r requirements.txt pyinstaller
    pause
    exit /b 1
)

echo Cleaning dist...
if exist ..\dist rmdir /s /q ..\dist

echo.
echo [1/4] VRainPrep...
"%PYINST%" VRainPrep.spec
if errorlevel 1 ( echo FAILED & pause & exit /b 1 )

echo.
echo [2/4] VRainStorm...
"%PYINST%" VRainStorm.spec
if errorlevel 1 ( echo FAILED & pause & exit /b 1 )

echo.
echo [3/4] VRainThiessen...
"%PYINST%" VRainThiessen.spec
if errorlevel 1 ( echo FAILED & pause & exit /b 1 )

echo.
echo [4/4] VRainFreq...
"%PYINST%" VRainFreq.spec
if errorlevel 1 ( echo FAILED & pause & exit /b 1 )

echo.
echo ============================================
echo  Done! File sizes:
echo ============================================
for %%f in (..\dist\VRainPrep.exe ..\dist\VRainStorm.exe ..\dist\VRainThiessen.exe ..\dist\VRainFreq.exe) do (
    if exist "%%f" for %%s in ("%%f") do echo   %%~nxf : %%~zs bytes
)
pause
