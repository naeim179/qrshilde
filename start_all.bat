@echo off

start "QRShilde Backend" cmd /k "cd /d D:\github-projects\qrshildessss\qrshilde && py -3.11 -m uvicorn qrshilde.api_app:app --reload --host 0.0.0.0 --port 8000"

timeout /t 4 >nul

start "QRShilde Flutter Web" cmd /k "cd /d D:\github-projects\qrshildessss\qrshilde\flutter_app && C:\Flutter\flutter\bin\flutter.bat run -d chrome"

exit