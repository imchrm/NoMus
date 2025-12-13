#!/bin/bash

# Script to run NoMus in DEVELOPMENT environment

echo "Starting NoMus in DEVELOPMENT mode..."
export ENV=development
poetry run python -m nomus.main
