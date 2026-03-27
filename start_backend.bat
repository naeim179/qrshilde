@echo off

cd /d D:\github-projects\qrshildessss\qrshilde

echo Starting Backend with Python 3.11...

py -3.11 -m uvicorn qrshilde.api_app:app --reload --host 0.0.0.0 --port 8000

pause