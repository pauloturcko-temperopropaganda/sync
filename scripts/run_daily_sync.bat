@echo off
cd /d "C:\dev\sync"
set PYTHONUTF8=1
echo. >> "C:\dev\sync\logs\daily_sync.log"
echo ============================================================ >> "C:\dev\sync\logs\daily_sync.log"
echo %date% %time% - iniciando sincronizacao diaria >> "C:\dev\sync\logs\daily_sync.log"
"C:\dev\sync\.venv\Scripts\python.exe" -m src.integrations.meta_ads.sync --days 7 >> "C:\dev\sync\logs\daily_sync.log" 2>&1
echo %date% %time% - fim (codigo de saida %errorlevel%) >> "C:\dev\sync\logs\daily_sync.log"
