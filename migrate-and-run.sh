#!/bin/bash

export FLASK_APP='frontpage:app' && \
flask db upgrade && \
gunicorn --bind 0.0.0.0:8080 -w 2 \
    --capture-output --access-logformat '%(r)s %(s)s' \
    --forwarded-allow-ips '0.0.0.0' \
    'frontpage:app'