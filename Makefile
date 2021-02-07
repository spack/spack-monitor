.PHONY: collect migrate migrations

# target: collect - calls the "collectstatic" django command
collect:
	python manage.py collectstatic --noinput

migrations: 
	python manage.py makemigrations

migrate: 
	python manage.py migrate

run: 
	python manage.py runserver

deploy:
	gcloud app deploy
