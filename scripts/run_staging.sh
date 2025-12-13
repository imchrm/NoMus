#!/bin/bash

# Script to run NoMus in STAGING environment

echo "Starting NoMus in STAGING mode..."
export ENV=staging
poetry run python -m nomus.main
