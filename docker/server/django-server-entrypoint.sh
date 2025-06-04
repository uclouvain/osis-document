#!/bin/bash

while true; do
  echo "[OSIS-Document] Re-starting Django runserver"
  python manage.py migrate
  python manage.py runserver 0.0.0.0:9503
  sleep 2
done