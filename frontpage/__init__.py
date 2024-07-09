import logging
import os
import re
import sys
from collections import Counter
from logging.handlers import RotatingFileHandler
from pathlib import Path

import click
from dotenv import load_dotenv
from flask import Flask, flash, redirect, request, url_for
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError
from sqlalchemy_utils import database_exists

from .db import db
from .models import Article, ArticleType, User

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

# Set up database URI
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "SQLALCHEMY_DATABASE_URI", f"sqlite:///{os.getcwd()}/blog.db"
)
# If it's a Postgres URI, replace the scheme with `postgresql+psycopg` because we're using the psycopg driver
if app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql://"):
    app.config["SQLALCHEMY_DATABASE_URI"] = app.config[
        "SQLALCHEMY_DATABASE_URI"
    ].replace("postgresql://", "postgresql+psycopg://", 1)

# Flask secret key
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "default-secret-key")

# S3 bucket config
app.config["USE_S3"] = os.environ.get("USE_S3", False)
app.config["S3_ENDPOINT"] = os.environ.get("S3_ENDPOINT", "default-s3-endpoint")
app.config["S3_BUCKET"] = os.environ.get("S3_BUCKET", "default-bucket-name")
app.config["S3_ACCESS_KEY"] = os.environ.get("S3_ACCESS_KEY", "default-access-key")
app.config["S3_SECRET_KEY"] = os.environ.get("S3_SECRET_KEY", "default-secret")
app.config["S3_CDN_ENDPOINT"] = os.environ.get(
    "S3_CDN_ENDPOINT", "default-cdn-endpoint"
)

# Setup the upload directory within the project directory
if not app.config["USE_S3"]:
    project_dir = os.path.dirname(
        os.path.abspath(__file__)
    )  # Directory where this file exists
    app.config["UPLOAD_FOLDER"] = os.path.join(project_dir, "static", "uploads")
    os.makedirs(
        app.config["UPLOAD_FOLDER"], exist_ok=True
    )  # Ensure the directory exists

db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)


def initialize_article_types():
    if not database_exists(app.config["SQLALCHEMY_DATABASE_URI"]):
        create_database(app.config["SQLALCHEMY_DATABASE_URI"])
    else:
        with app.app_context():
            if not ArticleType.query.first():  # This will check if the table is empty
                types = [
                    "Allegations of State Sponsorship",
                    "Banker's Box",
                    "Corporate",
                    "Cyberwar",
                    "Environmental",
                    "European Union",
                    "Extractivist Leaks",
                    "Fascist",
                    "Fuerzas Represivas",
                    "Greenhouse Project",
                    "Hack",
                    "Leak",
                    "Leak Markets",
                    "Limited Distribution",
                    "MilicoLeaks",
                    "News",
                    "Official",
                    "Opinion",
                    "Organization",
                    "Other",
                    "Ransomware",
                    "Researchers",
                    "Scrape",
                ]
                for type_name in types:
                    db.session.add(ArticleType(name=type_name))
                db.session.commit()


def parse_size(size_str):
    size_str = size_str.strip().upper()
    match = re.match(r"(\d{1,10}(\.\d{1,2})?)\s*(B|KB|MB|GB|TB)", size_str)

    if match is None:
        raise ValueError("Invalid size format")

    size, _, unit = match.groups()
    size = float(size)
    unit = unit.upper()

    if unit == "KB":
        return int(size * 1024)
    elif unit == "MB":
        return int(size * 1024**2)
    elif unit == "GB":
        return int(size * 1024**3)
    elif unit == "TB":
        return int(size * 1024**4)
    else:  # unit == 'B'
        return int(size)


# Convert bytes to human-readable format using decimal units
def format_size(size_in_bytes):
    if size_in_bytes < 1000:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1000**2:
        return f"{size_in_bytes / 1000:.2f} KB"
    elif size_in_bytes < 1000**3:
        return f"{size_in_bytes / 1000**2:.2f} MB"
    elif size_in_bytes < 1000**4:
        return f"{size_in_bytes / 1000**3:.2f} GB"
    else:
        return f"{size_in_bytes / 1000**4:.2f} TB"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    flash("⛔️ You need to be logged in to view that page.")
    return redirect(url_for("home"))


@app.context_processor
def inject_scopes():
    all_articles = Article.query.all()
    counter = Counter()
    for article in all_articles:
        for atype in article.article_types:
            counter[("type", atype.name)] += 1
        if article.country:
            for country in article.country.split(", "):
                counter[("country", country)] += 1
        if article.source:
            counter[("source", article.source)] += 1
    top_scopes = counter.most_common(5)
    return {
        "all_scopes": [
            {"type": scope[0][0], "name": scope[0][1]} for scope in top_scopes
        ]
    }


@app.context_processor
def inject_approval_count():
    if current_user.is_authenticated and current_user.is_admin:
        approval_count = Article.query.filter_by(pending_approval=True).count()
        return dict(approval_count=approval_count)
    return dict(approval_count=0)


@app.context_processor
def inject_team_link():
    show_team_link = User.query.filter_by(include_in_team_page=True).first() is not None
    return dict(show_team_link=show_team_link)


@app.cli.group(
    help="More DB management besides migration",
)
def db_extras() -> None:
    pass


@db_extras.command(help="Ensures all default article types are present")
def add_article_types():
    initialize_article_types()


@app.cli.group(help="Database management commands")
def db_manage():
    pass


@app.cli.command("add-type")
@click.argument("type_name")
def add_type(type_name):
    """Adds a new article type to the database using SQLAlchemy ORM."""
    if not type_name:
        click.echo("You must provide an article type name.", err=True)
        sys.exit(1)  # Properly exit with code 1 to indicate failure
    new_type = ArticleType(name=type_name)
    db.session.add(new_type)
    try:
        db.session.commit()
        click.echo(f"Successfully added new article type: '{type_name!r}'.")
    except IntegrityError as e:
        db.session.rollback()
        if "unique constraint" in str(e.orig).lower():
            click.echo(
                f"Failed to add new article type '{type_name!r}'. A type with this name already exists.",
                err=True,
            )
        else:
            click.echo(f"An unexpected database error occurred: {e}", err=True)
        sys.exit(1)  # Exit with code 1 on failure due to database errors


# Initialize logging
if not app.debug:
    file_handler = RotatingFileHandler(
        "app.log", maxBytes=1024 * 1024 * 100, backupCount=20
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

from . import routes  # noqa: F401 Import at end to avoid circular dependency issues
