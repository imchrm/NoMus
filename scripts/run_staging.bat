@echo off
REM Script to run NoMus in STAGING environment (Windows)

echo Starting NoMus in STAGING mode...
set ENV=staging
poetry run python -m nomus.main
