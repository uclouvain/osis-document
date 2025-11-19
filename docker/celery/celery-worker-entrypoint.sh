#!/bin/bash

while true; do
  echo "Re-start celery worker process"
  celery -A backoffice.celery worker --loglevel=info --concurrency=4
  sleep 2
done