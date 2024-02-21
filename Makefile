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

new-migration:
	docker-compose -f ./deployments/docker-compose.dev.yml exec backend alembic revision --autogenerate -m $(name)

upgrade-db:
	docker-compose -f ./deployments/docker-compose.dev.yml exec backend alembic upgrade $(revision)

downgrade-db:
	docker-compose -f ./deployments/docker-compose.dev.yml exec backend alembic downgrade -1
