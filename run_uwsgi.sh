#!/bin/bash

# Don't run these automatically for now
# python manage.py makemigrations users
# python manage.py makemigrations main
# python manage.py makemigrations
# python manage.py migrate auth
# python manage.py migrate
# python manage.py collectstatic --noinput
uwsgi nginx/uwsgi.ini
