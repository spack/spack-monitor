#!/bin/bash

# If the original migrations aren't run - do it.
# If you want to change models and run them again, you should run 
# these commands manually.
if [ ! -f "/opt/migrations-run" ]; then
    sleep 3
    python manage.py makemigrations users
    python manage.py makemigrations main
    python manage.py makemigrations
    python manage.py migrate users
    python manage.py migrate main
    python manage.py migrate auth
    python manage.py migrate 
    python manage.py collectstatic --noinput
    touch /opt/migrations-run
fi

# Kubernetes does not work with uwsgi
gunicorn --chdir /code --bind :3031 --workers 4 spackmon.wsgi
