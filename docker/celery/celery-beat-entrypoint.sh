#!/bin/bash

celery -A backoffice.celery beat -l info