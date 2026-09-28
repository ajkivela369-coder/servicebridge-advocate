@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title Forge Easy Installer
color 0B

echo ============================================================
echo                  FORGE EASY INSTALLER 0.5.6
echo ============================================================
echo.
echo This window only bootstraps Python, then opens the Forge GUI.
echo You do not need to open the _FORGE_INTERNAL folder.
echo.

set "PY_EXE="
call :FIND_PYTHON
if defined PY_EXE goto :LAUNCH_GUI

echo Python 3.12 with Tkinter was not found.
echo Installing the official Python 3.12 package with Windows Package Manager...
echo.
where winget >nul 2>&1
if errorlevel 1 goto :NO_WINGET

winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto :PY_FAIL

echo.
echo Python installer finished. Locating the new Python installation...
timeout /t 2 /nobreak >nul
call :FIND_PYTHON
if not defined PY_EXE goto :PY_NOT_FOUND

:LAUNCH_GUI
echo Found Python: %PY_EXE%
echo Opening Forge Setup...
echo.
"%PY_EXE%" "%~dp0_FORGE_INTERNAL\installer_gui.py"
set "ERR=%ERRORLEVEL%"
if not "%ERR%"=="0" (
  echo.
  echo Forge Setup closed with error code %ERR%.
  echo Please send a screenshot of this window and the Forge installer log.
  pause
)
exit /b %ERR%

:FIND_PYTHON
set "PY_EXE="
for /f "usebackq delims=" %%P in (`py -3.12 -c "import sys,tkinter; print(sys.executable)" 2^>nul`) do if not defined PY_EXE set "PY_EXE=%%P"
if defined PY_EXE if exist "%PY_EXE%" exit /b 0
set "PY_EXE="
for /f "usebackq delims=" %%P in (`python -c "import sys,tkinter; print(sys.executable)" 2^>nul`) do if not defined PY_EXE set "PY_EXE=%%P"
if defined PY_EXE if exist "%PY_EXE%" exit /b 0
set "PY_EXE="

for %%P in (
  "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
  "%ProgramFiles%\Python312\python.exe"
  "%ProgramFiles(x86)%\Python312\python.exe"
) do (
  if exist "%%~P" (
    "%%~P" -c "import tkinter" >nul 2>&1
    if not errorlevel 1 (
      set "PY_EXE=%%~P"
      exit /b 0
    )
  )
)

for /f "tokens=2,*" %%A in ('reg query "HKCU\Software\Python\PythonCore\3.12\InstallPath" /ve 2^>nul ^| find "REG_SZ"') do (
  if exist "%%Bpython.exe" (
    "%%Bpython.exe" -c "import tkinter" >nul 2>&1
    if not errorlevel 1 set "PY_EXE=%%Bpython.exe"
  )
)
if defined PY_EXE exit /b 0
for /f "tokens=2,*" %%A in ('reg query "HKLM\Software\Python\PythonCore\3.12\InstallPath" /ve 2^>nul ^| find "REG_SZ"') do (
  if exist "%%Bpython.exe" (
    "%%Bpython.exe" -c "import tkinter" >nul 2>&1
    if not errorlevel 1 set "PY_EXE=%%Bpython.exe"
  )
)
exit /b 0

:NO_WINGET
echo.
echo ERROR: Windows Package Manager ^(winget^) was not found.
echo Install/update "App Installer" from Microsoft Store and run INSTALL_FORGE again.
echo No Windows security setting needs to be disabled.
pause
exit /b 2

:PY_FAIL
echo.
echo ERROR: The Python installer returned an error.
echo Nothing else was changed. Please send a screenshot of this window.
pause
exit /b 3

:PY_NOT_FOUND
echo.
echo Python appears to have installed, but Forge could not locate it yet.
echo This can happen before Windows refreshes the Python registration.
echo.
echo Please CLOSE this window, then double-click INSTALL_FORGE again.
echo It should detect the Python installation and open Forge Setup immediately.
echo If it does not, send a screenshot of this message.
pause
exit /b 4
