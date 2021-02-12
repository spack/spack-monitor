#!/bin/bash

# If the original migrations aren't run - do it.
# If you want to change models and run them again, you should run 
# these commands manually.
if [ ! -f "/opt/migrations-run" ]; then
    python manage.py makemigrations users
    python manage.py makemigrations main
    python manage.py makemigrations
    python manage.py migrate auth
    python manage.py migrate 
    python manage.py collectstatic --noinput
    touch /opt/migrations-run
fi

uwsgi nginx/uwsgi.ini
