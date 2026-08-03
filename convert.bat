@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if exist "%~dp0.venv\Scripts\pythonw.exe" (
  start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0convert.py" %*
  goto :eof
)

if exist "%~dp0.venv\Scripts\python.exe" (
  start "" "%~dp0.venv\Scripts\python.exe" "%~dp0convert.py" %*
  goto :eof
)

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  start "" py -3 "%~dp0convert.py" %*
  goto :eof
)

where pythonw >nul 2>&1
if %ERRORLEVEL%==0 (
  start "" pythonw "%~dp0convert.py" %*
  goto :eof
)

where python >nul 2>&1
if %ERRORLEVEL%==0 (
  start "" python "%~dp0convert.py" %*
  goto :eof
)

echo Python bulunamadi. Python 3.10+ kurulu oldugundan ve PATH'te oldugundan emin olun.
pause
exit /b 1
