venv:
	rm -rf venv
	python -m venv venv
	./venv/bin/pip install -r requirements.txt

lint:
	./venv/bin/black --check -l 79 rchat
	./venv/bin/flake8 rchat
	./venv/bin/isort -c --src rchat --profile black -l 79 rchat

lint-win:
	./venv/Scripts/black --check -l 79 rchat
	./venv/Scripts/flake8 rchat
	./venv/Scripts/isort -c --src rchat --profile black -l 79 rchat

pretty-win:
	./venv/Scripts/black -l 79 rchat
	./venv/Scripts/flake8 rchat
	./venv/Scripts/isort --src rchat --profile black -l 79 rchat

dev-start:
	docker-compose -f deployments/docker-compose.dev.yml up --force-recreate --remove-orphans

dev-stop:
	docker-compose -f deployments/docker-compose.dev.yml down

dev-build:
	docker-compose -f deployments/docker-compose.dev.yml build --no-cache

start_postgres:
	docker-compose -f ./deployments/docker-compose.dev.yml up postgres > postgres_logs &

start_backend:
	docker-compose -f ./deployments/docker-compose.dev.yml up backend > rchat_logs &

run_registry:
	docker-compose -f ./deployments/registry/docker-compose.yml up -d
