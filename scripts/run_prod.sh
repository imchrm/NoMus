#!/bin/bash

# Script to run NoMus in PRODUCTION environment

echo "Starting NoMus in PRODUCTION mode..."
export ENV=production
poetry run python -m nomus.main
