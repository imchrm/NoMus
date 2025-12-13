@echo off
REM Script to run NoMus in DEVELOPMENT environment (Windows)

echo Starting NoMus in DEVELOPMENT mode...
set ENV=development
poetry run python -m nomus.main
