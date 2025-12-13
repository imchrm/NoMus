@echo off
REM Script to run NoMus in PRODUCTION environment (Windows)

echo Starting NoMus in PRODUCTION mode...
set ENV=production
poetry run python -m nomus.main
