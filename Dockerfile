FROM python:3.11-slim

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get -y dist-upgrade && \
    apt-get install -y \
    git \
    nginx

RUN pip install virtualenv

WORKDIR /frontpage

COPY . /frontpage

RUN rm -rf venv && virtualenv venv

RUN . venv/bin/activate && \
    pip install -U pip && \
    pip install -U poetry && \
    poetry self add poetry-plugin-export && \
    export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring && \
    poetry export --only main -f requirements.txt --output requirements.txt && \
    pip install -r requirements.txt && \
    pip install gunicorn

RUN touch .env && \
    if ! egrep -q '^FLASK_SECRET_KEY=' .env; then \
        echo 'Generating new secret key'; \
        FLASK_SECRET_KEY=$(openssl rand -hex 32); \
        echo "FLASK_SECRET_KEY=$FLASK_SECRET_KEY" >> .env; \
    fi

ENV FLASK_APP=frontpage:app

RUN . venv/bin/activate && \
    poetry run flask db upgrade && \
    poetry run flask db-extras add-article-types

RUN chown -R www-data:www-data /frontpage && \
    mkdir -p /frontpage/frontpage/static/uploads && \
    chown -R www-data:www-data /frontpage/frontpage/static/uploads && \
    chmod -R 755 /frontpage/frontpage/static/uploads

RUN apt-get install nginx -y && \
    cp files/nginx.conf /etc/nginx/sites-available/frontpage && \
    ln -sf /etc/nginx/sites-available/frontpage /etc/nginx/sites-enabled && \
    rm -f /etc/nginx/sites-available/default && \
    rm -f /etc/nginx/sites-enabled/default

EXPOSE 5000

CMD ["sh", "-c", ". venv/bin/activate && gunicorn --bind 0.0.0.0:5000 frontpage:app & nginx -g 'daemon off;'"]
