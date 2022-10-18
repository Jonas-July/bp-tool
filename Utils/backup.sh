#!/usr/bin/env bash
# Create a full db json dump
# execute as Utils/backup.sh target_name_to_export_to [--prod]

# abort on error, print executed commands
set -ex

# activate virtualenv if necessary
if [ -z ${VIRTUAL_ENV+x} ]; then
    source venv/bin/activate
fi

# set environment variable when we want to update in production
if [ "$3" = "--prod" ]; then
    export DJANGO_SETTINGS_MODULE=AKPlanning.settings_production
fi

mkdir -p ../backups/
python manage.py dumpdata --indent=2 > $1 --traceback
