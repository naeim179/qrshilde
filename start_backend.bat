@echo off
cd /d D:\github-projects\qrshildessss\qrshilde
call .venv\Scripts\activate
uvicorn qrshilde.api_app:app --reload --host 0.0.0.0 --port 8000
pause
