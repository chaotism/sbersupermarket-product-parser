FROM ultrafunk/undetected-chromedriver:3.20-chrome108

ENV SERVICE_NAME "sbermegamarket-parser"
ENV USER_HOME "/opt/$SERVICE_NAME"
ENV APP_PATH "$USER_HOME/application"


# Copy application
RUN set -ex && \
    mkdir -p  $USER_HOME
COPY ./  $USER_HOME


# Update chrome
RUN apt-get -y update \
    && apt-get -y install google-chrome-stable \
    && apt-get -y update  \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


# Install application dependencies TODO: add pip clear cache command
WORKDIR $USER_HOME
RUN set -ex && make init && make clear_cache

# Run application
WORKDIR $APP_PATH
CMD [ "sh", "-c", "poetry run python3 start_server.py"]
