#!/usr/bin/env bash
set -o errexit

python manage.py migrate --noinput

gunicorn videla.wsgi:application --bind 0.0.0.0:$PORT
