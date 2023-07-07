SHELL := /bin/bash

APP_PATH=./application
TEST_PATH=./tests

init:
	pip install poetry
	poetry install

clear_cache:
	poetry cache clear _default_cache --all  -n
	poetry cache clear pypi --all  -n

check-unused-code:
	vulture $(APP_PATH)

check-mypy:
	cd $(APP_PATH) && mypy .

check-pre-commit-hooks:
	poetry run pre-commit install && poetry run pre-commit run --all-files

run:
	export PYTHONPATH=$(APP_PATH) && set -a  && source .env && poetry run python $(APP_PATH)/start_server.py && set +a

test:
	export PYTHONPATH=$(APP_PATH) && set -a  && source .env && poetry run python -m pytest --cov=. --cov-report=xml --cov-append --no-cov-on-fail --verbose --color=yes $(TEST_PATH)

db-make-migration:
	export PYTHONPATH=$(APP_PATH) && set -a  && source .env && poetry run aerich migrate && set +a

db-migrate:
	export PYTHONPATH=$(APP_PATH) && set -a  && source .env && poetry run aerich upgrade && set +a

db-downgrade:
	export PYTHONPATH=$(APP_PATH) && set -a  && source .env && poetry run aerich downgrade --yes -v -1 && set +a

db-reset:
	export PYTHONPATH=$(APP_PATH) && set -a  && source .env && poetry run aerich downgrade --yes -v 0 && set +a

compose-build:
	docker-compose -f docker/docker-compose-dev.yml build  --compress

compose-up:
	docker-compose -f docker/docker-compose-dev.yml up

compose-stop:
	docker-compose -f docker/docker-compose-dev.yml stop

compose-destroy:
	docker-compose -f docker/docker-compose-dev.yml down  -v --remove-orphans

compose-shell:
	docker-compose -f docker/docker-compose-dev.yml run --rm api bash
