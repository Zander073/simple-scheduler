default: help

.PHONY: migrate
migrate:
	python manage.py migrate

.PHONY: seed
seed:
	python manage.py seed_data

.PHONY: start
start:
	python manage.py runserver

.PHONY: websocket
websocket:
	@uvicorn simple_scheduler.asgi:application --reload --port 8001
