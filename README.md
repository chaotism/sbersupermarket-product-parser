Small project for scrapping sberbank product data. Written with fast-api and ddd paradigm.


# Run from root folder
docker-compose  -f docker/docker-compose-dev.yml up


# Additional docs here
`docs/index.md`

# Plans
## Close plans
add supporting sql databases
add health check db and client
add cache
add seeding request with request_ids
add mypy to git-commit hooks (need fix issues)
migrate to python 3.11
use to python 3.11
use similar to https://hub.docker.com/r/ultrafunk/undetected-chromedriver docker container but much more thin
fix TODOS
check chromedrive and chrome versions for compatibility

## Future Plans
add try to different url upload policies (normal: This strategy causes Selenium to wait for the full page loading (html content and sub resources downloaded and parsed).
eager : This strategy causes Selenium to wait for the DOMContentLoaded event (html content downloaded and parsed only).
none : This strategy causes Selenium to return immediately after the initial page content is fully received (html content downloaded).)
add supporting sql databases
add search by entity fields
add chromium clients pool
add background task for updating outdated data
use remote webdrivers
