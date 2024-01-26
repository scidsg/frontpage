import logging
import os
import re
from collections import Counter
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, flash, redirect, request, url_for
from flask_login import LoginManager, current_user
from flask_migrate import Migrate

from .db import db
from .models import Article, ArticleType, User

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "SQLALCHEMY_DATABASE_URI", "sqlite:////var/www/html/frontpage/blog.db"
)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "default-secret-key")
app.config["UPLOAD_FOLDER"] = str(
    Path(
        os.environ.get("UPLOAD_FOLDER", "/var/www/html/frontpage/frontpage/static/uploads")
    ).absolute()
)

db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)


# Utility function to convert size strings to bytes
def parse_size(size_str):
    # Units for binary (base 2) and decimal (base 10) formats
    units_binary = {"B": 1, "KIB": 1024, "MIB": 1024**2, "GIB": 1024**3, "TIB": 1024**4}
    units_decimal = {"KB": 1000, "MB": 1000**2, "GB": 1000**3, "TB": 1000**4}

    # Make the string uppercase and remove spaces
    size_str = size_str.upper().replace(" ", "")

    # Regular expression to parse the size string
    matches = re.match(r"([0-9]*\.?[0-9]+)\s*([A-Z]+)", size_str)

    if not matches:
        raise ValueError("Invalid size format")

    size, unit = matches.groups()

    # Check if the unit is binary or decimal and calculate accordingly
    if unit in units_binary:
        return int(float(size) * units_binary[unit])
    elif unit in units_decimal:
        return int(float(size) * units_decimal[unit])
    else:
        raise ValueError("Unknown size unit")


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


@app.errorhandler(404)
def page_not_found(e):
    if request.path.startswith("/static/"):
        # If it's a static file, just return the default 404 response
        return e
    flash("⛔️ That page doesn't exist", "warning")
    return redirect(url_for("home"))


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
        # Count article types using the new many-to-many relationship
        for atype in article.article_types:
            counter[("type", atype.name)] += 1

        # Count countries (no change here)
        if article.country:
            for country in article.country.split(", "):
                counter[("country", country)] += 1

        # Count sources (no change here)
        if article.source:
            counter[("source", article.source)] += 1

    # Retrieve the top 5 scopes
    top_scopes = counter.most_common(5)
    all_scopes = [{"type": scope[0][0], "name": scope[0][1]} for scope in top_scopes]
    return {"all_scopes": all_scopes}


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


def initialize_article_types():
    existing_types = [atype.name for atype in ArticleType.query.all()]
    for atype in [
        "Allegations of State Sponsorship",
        "Banker's Box",
        "Corporate",
        "Cyberwar",
        "Environmental",
        "European Union",
        "Extractivist Leaks",
        "Fascist",
        "Fuerzas Represivas",
        "Hack",
        "Leak",
        "Leak Markets",
        "Limited Distribution",
        "News",
        "Opinion",
        "Organization",
        "Other",
        "Ransomware",
        "Researchers",
        "Scrape",
    ]:
        if atype not in existing_types:
            new_type = ArticleType(name=atype)
            db.session.add(new_type)
    db.session.commit()


# Initialize logging
if not app.debug:
    file_handler = RotatingFileHandler("app.log", maxBytes=1024 * 1024 * 100, backupCount=20)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)


from . import routes  # noqa: # import at end of module to force routes to populate
