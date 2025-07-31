@echo off
setlocal

REM Cambia al directorio de tu proyecto Flask
cd /d C:\ruta\a\tu\proyecto

REM Inicia Flask en segundo plano
start "" cmd /k "python app.py"

REM Espera unos segundos a que Flask inicie
timeout /t 5 > nul

REM Cambia a la carpeta donde está ngrok
cd /d D:\Downloads\ngrok-v3-stable-windows-amd64

REM Inicia ngrok en el puerto 5000
start "" cmd /k "ngrok http 5000"

exit
