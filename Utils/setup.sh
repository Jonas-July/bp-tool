#!/usr/bin/env bash
# Setup
# execute as Utils/setup.sh

# abort on error, print executed commands
set -ex

# remove old virtualenv
rm -rf venv/

# set environment variable when we want to update in production
if [ "$1" = "--prod" ]; then
    export DJANGO_SETTINGS_MODULE=bptool.settings_production
fi

# Setup Python Environment
# Requires: Virtualenv, appropriate Python installation
virtualenv venv -p python3
source venv/bin/activate
pip install --upgrade setuptools pip wheel
pip install -r requirements.txt

# Setup database
python manage.py migrate

# Prepare static files and translations
python manage.py collectstatic --noinput

# Create superuser
# Credentials are entered interactively on CLI
python manage.py createsuperuser

deactivate
