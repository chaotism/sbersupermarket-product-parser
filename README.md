Small project for scrapping sberbank product data. Written with fast-api and ddd paradigm.

# Installation
make init


# Run
make run


# Test
make test


# Migration
make db_make_migration
make db_migrate


# Compose run
make compose_build
make compose_up


# The project structure

`application/main_web.py` file for start server instead `uvicorn` load.
`application/clients` folder for external data resource clients.
`application/common` folder for common stuff like utils, constants, etc.
`application/domain` folder for business logic of application.
`application/infrastructure` folder for infrastructure stuff like health checks etc.
`application/storages` folder for db adapters.
`application/web` folder for web server logic of application.
`tests` folder for tests.


# Plans
## Close plans
- add CI
- clear commit history
- add cache
- add mypy to git-commit hooks (need fix issues)
- migrate to python 3.11
- use to python 3.11
- use similar to https://hub.docker.com/r/ultrafunk/undetected-chromedriver docker container but much more thin
- check docker build logic
- fix TODOS


## Future Plans
- add try to different url upload policies (normal: This strategy causes Selenium to wait for the full page loading (html content and sub resources downloaded and parsed).
eager : This strategy causes Selenium to wait for the DOMContentLoaded event (html content downloaded and parsed only).
none : This strategy causes Selenium to return immediately after the initial page content is fully received (html content downloaded).)
- add supporting sql databases
- add search by entity fields
- add chromium clients pool
- add background task for updating outdated data
- use remote webdrivers
