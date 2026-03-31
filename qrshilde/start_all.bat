@echo off

echo ===============================
echo Starting QRShilde System...
echo ===============================

REM 🔥 تشغيل Backend مع venv
start "QRShilde Backend" cmd /k ^
"cd /d D:\github-projects\qrshildessss\qrshilde && ^
call .venv\Scripts\activate && ^
python -m uvicorn qrshilde.api_app:app --reload --host 0.0.0.0 --port 8000"

REM ⏳ انتظار بسيط
timeout /t 4 >nul

REM 🌐 تشغيل Flutter Web
start "QRShilde Flutter Web" cmd /k ^
"cd /d D:\github-projects\qrshildessss\qrshilde\flutter_app && ^
C:\Flutter\flutter\bin\flutter.bat run -d chrome"

exit