@echo off
cd /d "%~dp0"
py -3 --version >nul 2>&1
if errorlevel 1 (
  echo Instale o Python 3 no Windows e tente novamente.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 goto falha
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto falha
.venv\Scripts\python.exe pastel.py
if errorlevel 1 goto falha
exit /b 0
:falha
echo Nao foi possivel iniciar. Confira a mensagem acima.
pause
exit /b 1
