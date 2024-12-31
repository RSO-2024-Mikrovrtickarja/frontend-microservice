#!/usr/bin/env bash
set -ex

#mkdir /app/backend
#cd /app/backend

#echo "Migrating database..."
#/root/.local/bin/poetry run python manage.py migrate

echo "Running server..."
/root/.local/bin/poetry run python manage.py runserver --skip-checks --noreload 0.0.0.0:8000