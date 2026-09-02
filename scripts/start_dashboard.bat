@echo off
cd /d "C:\dev\sync"
set PYTHONUTF8=1
echo Iniciando o painel do Sync em http://localhost:8050 ...
echo (deixa essa janela aberta enquanto estiver usando o painel; feche pra desligar)
"C:\dev\sync\.venv\Scripts\python.exe" -m src.dashboard.app
