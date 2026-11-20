@echo off
rem Inicia o assistente R2D2 com o ambiente virtual do projeto (Windows).
rem A porta do Arduino e detectada sozinha; para fixar, defina ARDUINO_PORT antes.
rem Criar o arquivo controle\parar encerra o assistente como no "dedao sair".
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Ambiente virtual nao encontrado. Siga a secao "Instalacao" do README.
    pause
    exit /b 1
)
chcp 65001 > nul
set PYTHONUTF8=1
if not exist controle mkdir controle
if exist controle\parar del controle\parar
set "R2D2_ARQUIVO_PARADA=%~dp0controle\parar"
".venv\Scripts\python.exe" checkpoint_alexa.py
pause
