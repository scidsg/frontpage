# First stage: Installing Poetry and exporting dependencies
FROM python:3.11-slim as builder

ARG DEBIAN_FRONTEND=noninteractive
ARG FLASK_SECRET_KEY
ARG FERNET_KEY

# Update system and install Poetry
RUN apt-get update && \
    apt-get -y dist-upgrade && \
    apt-get install -y curl && \
    pip install -U pip poetry

# Set work directory and copy source code
WORKDIR /build
COPY . /build

# Setup the Python environment, install dependencies using Poetry
RUN poetry config virtualenvs.create false && \
    poetry install && \
    export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring && \
    poetry export --format=requirements.txt --output=/build/requirements.txt --without-hashes

# Second stage: Setup the production container
FROM python:3.11-slim as production

ARG DEBIAN_FRONTEND=noninteractive
ARG FERNET_KEY

# Install system dependencies
RUN apt-get update && \
    apt-get -y dist-upgrade && \
    apt-get install -y nginx supervisor

# Copy the requirements.txt from the builder stage
COPY --from=builder /build/requirements.txt /requirements.txt

# Install Python dependencies from the requirements file
RUN pip install -U pip && \
    pip install -r /requirements.txt

WORKDIR /frontpage

# Copy only the necessary application files
COPY . /frontpage

# Prepare supervisord configuration
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Set environment variables
ENV FLASK_APP=frontpage:app
ENV FERNET_KEY=${FERNET_KEY}

# Ensure the uploads directory exists
RUN mkdir -p /frontpage/frontpage/static/uploads

# Configure Nginx
RUN cp /frontpage/files/nginx.conf /etc/nginx/sites-available/frontpage && \
    ln -sf /etc/nginx/sites-available/frontpage /etc/nginx/sites-enabled && \
    rm -f /etc/nginx/sites-available/default && \
    rm -f /etc/nginx/sites-enabled/default

# Expose port 8000 for the application
EXPOSE 8000

# Command to run when the container starts
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
