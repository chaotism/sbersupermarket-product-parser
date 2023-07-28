# sbermegamarket product scrapper

Используется Python3.9

## Установка

1. Используется Python3.9
   Debian
     ```sh
    curl https://pyenv.run | bash
    pyenv install --list
    pyenv install 3.9.9
    pyenv global 3.9.9
    ```
   MacOs:
   ```sh
   brew install --cask pyenv
   ```

2. Для проекта необходимо установить chrome
   Debian
    ```sh
    curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub |  sudo apt-key add -
    echo "deb [arch=amd64]  http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
    apt-get -y update
    apt-get -y install google-chrome-stable
   ```
   MacOs
   ```sh
   brew install --cask google-chrome
   ```
   или скачать его с оффицального сайта под вашу платформу

3. Устанавливаем [poetry](https://python-poetry.org) и зависимости проекта

    ```sh
    make init
    ```
   Если возникает ошибка сертификатов то поможет эти два решения:
    ```sh
    export CURL_CA_BUNDLE=
    ```
    + скачать сертификаты точки для нексуса и добавить их
    ```sh
    export REQUESTS_CA_BUNDLE=PATH_TO_CERT
    ```

4. Подключаем pre-commit hooks

    ```bash
   make check-pre-commit-hooks
    ```

5. Собираем приложение при помощи docker build
   копируем необходимые для доступа к nexus сертификаты в папку certs
    ```sh
    make compose-build
    ```

6. Запускаем приложение и PostgreSQL при помощи docker compose
   ```sh
   make compose-up
   ```
   или частями
   копируем `.env.example` в файл `.env`
   исправляем параметры `.env` на локальные.
   ```sh
   docker-compose -f docker/docker-compose-dev.yml up postgres
   make run
   ```

7. Накатываем миграции

    ```sh
   make db-migrate
   ```
   Если надо сгенерить новые
   ```sh
   make db-make-migration
   ```
   Откатить
   ```sh
   make db-downgrade
   ```

8. Запуск тестов
   копируем `.env.example` в файл `.env.test`
   исправляем параметры `.env` на локальные.
   ```sh
   make test
   ```

9. Доп команды
   Поиск неиспользуемого кода
   ```sh
   make check-unused-code
   ```

10. Структура проекта
- `application/main_web.py` файл запуска если запускать вместо `uvicorn` load.
- `application/clients` клиенты для внешних сервисов и сайтов.
- `application/common` общая папка с утилитами и константами
- `application/domain` бизнес логика и бизнес сущности.
- `application/infrastructure` инфраструктурный код типа хелс чеков и тд.
- `application/storages` адаптеры к базам данным.
- `application/web` основная логика фаст апи веб приложения.
- `tests` тесты.

11. Основные ручки эндпоинтов
- `POST /api/v1/product_info/manual_upload_products` - ручная загрузка данные (если нужно подтянуть данные с другого инстанса)
- `POST /api/v1/product_info/seed_data` - принудительное обновление данных со сбермегамаркета (если данные устарели)
- `GET /api/v1/product_info/{goods_id}` - получение данных по товару (берется из базы, если нет тянеться со сбера)
- `POST /api/v1/product_info/{goods_id}` - сохранение данных по товару из сохраненной html страницы
- `GET /api/v1/product_info/category/{category_name}` - получение данных по товарам с указанной категорией
- `GET /api/v1/product_info/count` - получениданных по количеству товаров в базе(полезно для дебага)

- `GET /health/ping` - проверка сервиса, может заменять liveness-probe
- `GET /health/system-status` - получение информации по сервису (дебаг режим, версия апи)

12. Проблемы
- На маках с m1 будет некорректно работать контейнер с app в для команды `make compose-up` рекомендуется запускать отдельно postgres и make run 
- Версия хрома может протухать по отношению к хроме драйверу -- раз в мясяц лучше пересобирать образ или использовать SBER_PARSER_CHROME_VERSION
- Хром может крашится без причины, стоит посмотреть какие лимиты у контейнера и поиграть с настройками SBER_PARSER_EXPERIMENTAL/SBER_PARSER_POOL_FASTLOAD
- Скрапер может баниться попробуйте посмотреть SBER_PARSER_POOL_HAS_PROXY / SBER_PARSER_POOL_RANDOM_USERAGENT / SBER_PARSER_CHROME_USER_DIR для clients/parser/proxies.py и clients/parser/useragent.py 
- Папка log может забиваться рекомендую отключать API_DEBUG
- Адрес до сервера Sentry указывается через SENTRY_DSN
- Если TOKENS пустые авторизации для запросов нет
- Если есть проблемы с сертификатами при запуске приложения/тестов [SSL: CERTIFICATE_VERIFY_FAILED] -- то надо посмотреть глобавльные переменные CURL_CA_BUNDLE= REQUESTS_CA_BUNDLE= и решение https://jcutrer.com/python/requests-ignore-invalid-ssl-certificates
