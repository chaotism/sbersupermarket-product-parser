- Small project for scrapping sberbank product data. Written with fast-api and ddd paradigm.

# Installation
## Debian
- curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub |  sudo apt-key add -
- echo "deb [arch=amd64]  http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
- apt-get -y update
- apt-get -y install google-chrome-stable

## Common part
- make init


# Run
- copy .env.example to .env
- make compose_up
- make run


# Test
- copy .env.example to .test.env
- make compose_up
- make test


# Migration
- make db_make_migration
- make db_migrate


# Compose run
- make compose_build
- make compose_up


# The project structure

- `application/main_web.py` file for start server instead `uvicorn` load.
- `application/clients` folder for external data resource clients.
- `application/common` folder for common stuff like utils, constants, etc.
- `application/domain` folder for business logic of application.
- `application/infrastructure` folder for infrastructure stuff like health checks etc.
- `application/storages` folder for db adapters.
- `application/web` folder for web server logic of application.
- `tests` folder for tests.


# Plans
## Close plans
- add CI
- add cache
- add mypy to git-commit hooks (need fix issues)
- fix TODOS


## Future Plans
- add search by entity fields
- add background task for updating outdated data
