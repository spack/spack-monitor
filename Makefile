.PHONY: build collect migrate migrations run

# Intended to be run outside of container
build: 
	docker-compose build


# intended to be run inside the django container
collect:
	python manage.py collectstatic --noinput

migrations: 
	python manage.py makemigrations

migrate: 
	python manage.py migrate

run: 
	python manage.py runserver
