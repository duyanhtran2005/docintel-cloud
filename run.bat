@echo off
set PYTHONPATH=src
python -m uvicorn src.api.main:app --reload --port 8000
pause