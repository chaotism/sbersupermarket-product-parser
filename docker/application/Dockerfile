FROM ultrafunk/undetected-chromedriver:3.20-chrome108

ENV SERVICE_NAME "sbermegamarket-parser"
ENV USER_HOME "/opt/$SERVICE_NAME"
ENV APP_PATH "$USER_HOME/application"

# Update chrome
RUN apt-get -y update \
    && apt-get -y install google-chrome-stable \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


# Install application dependencies TODO: add pip clear cache command
RUN mkdir -p $USER_HOME/
WORKDIR $USER_HOME
COPY ./Makefile ./pyproject.toml ./poetry.lock $USER_HOME/
RUN make install && make clear_cache

# Copy application
COPY ./  $USER_HOME
# Run application
WORKDIR $APP_PATH
CMD [ "sh", "-c", "poetry run python3 start_server.py"]
