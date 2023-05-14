FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

ENV SERVICE_NAME "sbersupermarket-parser"
ENV USER_HOME "/opt/$SERVICE_NAME"
ENV APP_PATH "$USER_HOME/application"

# Copy application
RUN set -ex && \
    mkdir -p  $USER_HOME
COPY ./  $USER_HOME

# Install chrome driver TODO: add clear apt-get cache
RUN curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN echo "deb [arch=amd64]  http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list

RUN apt-get clean \
    && apt-get -y update  \
    && apt-get -y install google-chrome-stable \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN wget https://chromedriver.storage.googleapis.com/2.41/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && rm chromedriver_linux64.zip \
    && mv chromedriver /usr/bin/chromedriver \
    && chown root:root /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver

# Install application dependencies TODO: add pip clear cache command
WORKDIR $USER_HOME
RUN set -ex && make init

# Run application
WORKDIR $APP_PATH
CMD [ "sh", "-c", "poetry run python3 start_server.py"]
