from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from datetime import datetime
from logging.handlers import RotatingFileHandler
import logging
import os
import markdown
import pycountry
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    TextAreaField,
    BooleanField,
)
from wtforms.validators import (
    DataRequired,
    EqualTo,
    ValidationError,
    Length,
    Regexp,
    URL,
    Optional,
)
from werkzeug.utils import secure_filename
from flask_wtf.file import FileField, FileAllowed
from collections import Counter
from itertools import groupby
from slugify import slugify
from sqlalchemy.exc import IntegrityError


load_dotenv()  # Load environment variables from .env file

# Uploads
UPLOAD_FOLDER = "/var/www/html/frontpage/static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

# Initialize Flask app and database
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////var/www/html/frontpage/blog.db"
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "default-secret-key")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Association table for articles and article types
article_article_types = db.Table(
    "article_article_types",
    db.Column("article_id", db.Integer, db.ForeignKey("article.id"), primary_key=True),
    db.Column(
        "article_type_id",
        db.Integer,
        db.ForeignKey("article_type.id"),
        primary_key=True,
    ),
)


# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(100))
    bio = db.Column(db.Text)
    include_in_team_page = db.Column(db.Boolean, default=False)
    display_name = db.Column(db.String(100), nullable=True)
    custom_url = db.Column(db.String(255), nullable=True)
    avatar = db.Column(db.String(255), nullable=True)
    requires_approval = db.Column(db.Boolean, default=False, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

    def __repr__(self):
        return "<Category %r>" % self.name


# Association table for the many-to-many relationship
article_categories = db.Table(
    "article_categories",
    db.Column("article_id", db.Integer, db.ForeignKey("article.id"), primary_key=True),
    db.Column(
        "category_id", db.Integer, db.ForeignKey("category.id"), primary_key=True
    ),
)


# Define the Article model
class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(50), nullable=False)
    publish_date = db.Column(db.DateTime, default=datetime.utcnow)
    country = db.Column(db.String(50))
    download_link = db.Column(db.String(255))
    download_link2 = db.Column(db.String(255))
    download_link3 = db.Column(db.String(255))
    magnet_link = db.Column(db.String(255))
    magnet_link2 = db.Column(db.String(255))
    magnet_link3 = db.Column(db.String(255))
    torrent_link = db.Column(db.String(255))
    torrent_link2 = db.Column(db.String(255))
    torrent_link3 = db.Column(db.String(255))
    ipfs_link = db.Column(db.String(255))
    ipfs_link2 = db.Column(db.String(255))
    ipfs_link3 = db.Column(db.String(255))
    download_size = db.Column(db.String(255))
    external_collaboration = db.Column(db.String(255))
    external_collaboration2 = db.Column(db.String(255))
    external_collaboration3 = db.Column(db.String(255))
    article_type = db.Column(db.String(50))
    source = db.Column(db.String(255))
    last_edited = db.Column(db.DateTime)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    pending_approval = db.Column(db.Boolean, default=False, nullable=False)
    categories = db.relationship(
        "Category",
        secondary=article_categories,
        lazy="subquery",
        backref=db.backref("articles", lazy=True),
    )
    article_types = db.relationship(
        "ArticleType",
        secondary=article_article_types,
        lazy="subquery",
        backref=db.backref("articles", lazy=True),
    )

    def __repr__(self):
        return "<Article %r>" % self.title

    def set_slug(self):
        if not self.slug:
            self.slug = slugify(self.title)


class ArticleType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

    def __repr__(self):
        return "<ArticleType %r>" % self.name


class InvitationCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False, unique=True)
    used = db.Column(db.Boolean, default=False, nullable=False)
    expiration_date = db.Column(db.DateTime, nullable=False)  # Add this line

    def __repr__(self):
        return f"<InvitationCode {self.code}>"


class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters long."),
            Regexp(r"(?=.*[A-Za-z])", message="Password must contain letters."),
            Regexp(r"(?=.*[0-9])", message="Password must contain numbers."),
            Regexp(
                r"(?=.*[-!@#$%^&*()_+])",
                message="Password must contain at least one special character (-!@#$%^&*()_+).",
            ),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    invite_code = StringField("Invite Code", validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                "That username is already taken. Please choose a different one."
            )

    def validate_invite_code(self, invite_code):
        code = InvitationCode.query.filter_by(code=invite_code.data, used=False).first()
        if not code:
            raise ValidationError("Invalid or expired invite code.")


class BioForm(FlaskForm):
    bio = TextAreaField(
        "Bio", render_kw={"placeholder": "Tell us something about yourself"}
    )
    submit_bio = SubmitField("Update Bio")


class PasswordForm(FlaskForm):
    current_password = PasswordField(
        "Current Password",
        validators=[DataRequired()],
        render_kw={"placeholder": "Current Password"},
    )
    new_password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters long."),
            Regexp(r"(?=.*[A-Za-z])", message="Password must contain letters."),
            Regexp(r"(?=.*[0-9])", message="Password must contain numbers."),
            Regexp(
                r"(?=.*[-!@#$%^&*()_+])",
                message="Password must contain at least one special character (-!@#$%^&*()_+).",
            ),
        ],
        render_kw={"placeholder": "New Password"},
    )
    confirm_new_password = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(),
            EqualTo("new_password", message="Passwords must match."),
        ],
        render_kw={"placeholder": "Confirm New Password"},
    )
    submit_password = SubmitField("Update Password")


class DisplayNameForm(FlaskForm):
    display_name = StringField(
        "Display Name",
        validators=[Length(max=100)],
        render_kw={"placeholder": "Enter a display name"},
    )
    submit_display_name = SubmitField("Update Display Name")


class TeamPageForm(FlaskForm):
    include_in_team_page = BooleanField("Include in Team Page", default=False)
    submit_team = SubmitField("Update Team Setting")


class CustomUrlForm(FlaskForm):
    custom_url = StringField(
        "Custom URL",
        validators=[Optional(), URL(message="Must be a valid URL.")],
        render_kw={"placeholder": "Enter your custom URL"},
    )
    submit_custom_url = SubmitField("Update Custom URL")


class AvatarForm(FlaskForm):
    avatar = FileField(
        "Avatar", validators=[FileAllowed(["jpg", "png"], "Images only!")]
    )
    submit_avatar = SubmitField("Upload Avatar")


@app.errorhandler(404)
def page_not_found(e):
    path = request.path
    # Check if the missing resource is not a static file
    if not path.startswith("/static/"):
        # Flash a message to the user
        flash("⛔️ That page doesn't exist", "warning")
        # Redirect to home page
        return redirect(url_for("home"))
    # If it's a static file, just return the default 404 response
    return e


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    # Flash a message to inform the user
    flash("⛔️ You need to be logged in to view that page.")
    return redirect(url_for("home"))


@app.context_processor
def inject_scopes():
    all_articles = Article.query.all()
    counter = Counter()
    for article in all_articles:
        if article.article_type:
            counter[("type", article.article_type)] += 1
        if article.country:
            for country in article.country.split(", "):
                counter[("country", country)] += 1
        if article.source:
            counter[("source", article.source)] += 1

    top_scopes = counter.most_common(5)
    all_scopes = [{"type": scope[0][0], "name": scope[0][1]} for scope in top_scopes]
    return {"all_scopes": all_scopes}


@app.context_processor
def inject_approval_count():
    if current_user.is_authenticated and current_user.is_admin:
        approval_count = Article.query.filter_by(pending_approval=True).count()
        return dict(approval_count=approval_count)
    return dict(approval_count=0)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = RegistrationForm()
    if form.validate_on_submit():
        invite_code = InvitationCode.query.filter_by(
            code=form.invite_code.data, used=False
        ).first()
        if not invite_code:
            flash("⛔️ Invalid or expired invite code.", "danger")
            return render_template("register.html", title="Register", form=form)

        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, password_hash=hashed_password)
        db.session.add(user)

        # Mark invite code as used
        invite_code.used = True
        db.session.commit()

        flash("👍 Your account has been created! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", title="Register", form=form)


# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("home"))
        flash("⛔️ Invalid username or password")

    return render_template("login.html")


# Logout route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.context_processor
def inject_team_link():
    show_team_link = User.query.filter_by(include_in_team_page=True).first() is not None
    return dict(show_team_link=show_team_link)


@app.route("/")
def home():
    max_articles = 10

    # Only fetch articles that are not pending approval
    main_articles = (
        Article.query.filter_by(pending_approval=False)
        .order_by(Article.publish_date.desc())
        .limit(max_articles)
        .all()
    )

    main_articles_total = Article.query.count()

    recently_edited_articles = (
        Article.query.filter(Article.last_edited != None)
        .order_by(Article.last_edited.desc())
        .limit(max_articles)
        .all()
    )
    recently_edited_articles_total = Article.query.filter(
        Article.last_edited != None
    ).count()

    external_collaboration_articles = (
        Article.query.filter(Article.external_collaboration != None)
        .filter(Article.external_collaboration != "")
        .order_by(Article.publish_date.desc())
        .limit(max_articles)
        .all()
    )
    external_collaboration_articles_total = (
        Article.query.filter(Article.external_collaboration != None)
        .filter(Article.external_collaboration != "")
        .count()
    )

    show_team_link = User.query.filter_by(include_in_team_page=True).first() is not None

    return render_template(
        "home.html",
        main_articles=main_articles,
        main_articles_total=main_articles_total,
        main_articles_more=main_articles_total > max_articles,
        recently_edited_articles=recently_edited_articles,
        recently_edited_articles_total=recently_edited_articles_total,
        recently_edited_articles_more=recently_edited_articles_total > max_articles,
        external_collaboration_articles=external_collaboration_articles,
        external_collaboration_articles_total=external_collaboration_articles_total,
        external_collaboration_articles_more=external_collaboration_articles_total
        > max_articles,
        show_team_link=show_team_link,
    )


# Protect the publish route
@app.route("/publish", methods=["GET", "POST"])
@login_required
def publish():
    categories = Category.query.all()
    countries = [country.name for country in pycountry.countries]
    article_types = ArticleType.query.all()  # Fetch article types from the database

    if request.method == "POST":
        article_title = request.form["title"]
        article_content = request.form["content"]
        article_countries = request.form.getlist("countries")
        article_country = ", ".join(article_countries)
        selected_article_type_ids = request.form.getlist("article_types")
        selected_article_types = ArticleType.query.filter(
            ArticleType.id.in_(selected_article_type_ids)
        ).all()
        article_download_link = request.form["download_link"]
        article_download_link2 = request.form["download_link2"]
        article_download_link3 = request.form["download_link3"]
        article_magnet_link = request.form["magnet_link"]
        article_magnet_link2 = request.form["magnet_link2"]
        article_magnet_link3 = request.form["magnet_link3"]
        article_torrent_link = request.form["torrent_link"]
        article_torrent_link2 = request.form["torrent_link2"]
        article_torrent_link3 = request.form["torrent_link3"]
        article_ipfs_link = request.form["ipfs_link"]
        article_ipfs_link2 = request.form["ipfs_link2"]
        article_ipfs_link3 = request.form["ipfs_link3"]
        article_download_size = request.form["download_size"]
        article_external_collaboration = request.form.get("external_collaboration")
        article_external_collaboration2 = request.form.get("external_collaboration2")
        article_external_collaboration3 = request.form.get("external_collaboration3")
        article_source = request.form["source"]
        requires_approval = current_user.requires_approval

        new_article = Article(
            title=article_title,
            content=article_content,
            author=current_user.username,
            country=article_country,
            download_link=article_download_link,
            download_link2=article_download_link2,
            download_link3=article_download_link3,
            article_types=selected_article_types,
            magnet_link=article_magnet_link,
            magnet_link2=article_magnet_link2,
            magnet_link3=article_magnet_link3,
            torrent_link=article_torrent_link,
            torrent_link2=article_torrent_link2,
            torrent_link3=article_torrent_link3,
            ipfs_link=article_ipfs_link,
            ipfs_link2=article_ipfs_link2,
            ipfs_link3=article_ipfs_link3,
            download_size=article_download_size,
            external_collaboration=article_external_collaboration,
            external_collaboration2=article_external_collaboration2,
            external_collaboration3=article_external_collaboration3,
            source=article_source,
            pending_approval=requires_approval,
        )

        # Extract and handle the publication date
        publish_date_str = request.form.get("publish_date")
        if publish_date_str:
            publish_date = datetime.strptime(publish_date_str, "%Y-%m-%dT%H:%M")
            new_article.publish_date = publish_date
        else:
            new_article.publish_date = datetime.utcnow()  # default to current time

        # Set slug for the new article
        new_article.set_slug()

        # Handle the last_edited date
        last_edited_str = request.form.get("last_edited")
        if last_edited_str:
            last_edited = datetime.strptime(last_edited_str, "%Y-%m-%dT%H:%M")
            new_article.last_edited = last_edited

        # Handle article categories
        selected_category_ids = request.form.getlist("categories")
        selected_categories = Category.query.filter(
            Category.id.in_(selected_category_ids)
        ).all()
        new_article.categories = selected_categories

        try:
            db.session.add(new_article)
            db.session.commit()

            flash_message = (
                "⏱️ Your article has been submitted for approval."
                if requires_approval
                else "👍 Article published successfully."
            )
            flash(flash_message, "success")
        except IntegrityError:
            db.session.rollback()
            flash(
                "An error occurred: The article slug must be unique. Please try a different title.",
                "danger",
            )
            app.logger.error(
                "IntegrityError: Duplicate slug found while trying to publish an article."
            )
            return redirect(url_for("publish"))

        return redirect(url_for("home"))

    return render_template(
        "publish.html",
        categories=categories,
        countries=countries,
        article_types=article_types,  # Pass article types to the template
    )


@app.route("/approve_articles")
@login_required
def approve_articles():
    if not current_user.is_admin:
        flash("⛔️ Unauthorized access.", "danger")
        return redirect(url_for("home"))

    # Fetch only articles that are pending approval
    articles_to_approve = Article.query.filter_by(pending_approval=True).all()
    article_count = len(
        articles_to_approve
    )  # Get the count of articles pending approval

    return render_template(
        "approve_articles.html",
        articles=articles_to_approve,
        article_count=article_count,
    )


@app.route("/approve_article/<slug>", methods=["POST"])
@login_required
def approve_article(slug):
    if not current_user.is_admin:
        flash("⛔️ Unauthorized access.", "danger")
        return redirect(url_for("home"))

    article = Article.query.filter_by(slug=slug).first_or_404()
    if current_user.is_admin:
        article.pending_approval = False  # Mark as approved
        db.session.commit()
        flash("🎉 Article approved.", "success")
    else:
        flash("⛔️ Unauthorized access.", "danger")

    return redirect(url_for("approve_articles"))


@app.route("/users", methods=["GET", "POST"])
@login_required
def users():
    if not current_user.is_admin:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("home"))

    if request.method == "POST":
        all_users = User.query.all()
        for user in all_users:
            user.requires_approval = f"approval_{user.id}" in request.form
            user.is_admin = f"admin_{user.id}" in request.form
        db.session.commit()
        flash("👍 Users updated successfully.", "success")

    all_users = User.query.all()
    user_count = len(all_users)  # Get the count of users
    return render_template("users.html", users=all_users, user_count=user_count)


@app.route("/article/<slug>")
def article(slug):
    article = Article.query.filter_by(slug=slug).first_or_404()
    content_html = markdown.markdown(article.content)

    # Fetch related articles by type
    related_by_type = (
        Article.query.join(Article.article_types)
        .filter(
            ArticleType.id.in_([atype.id for atype in article.article_types]),
            Article.id != article.id,
        )
        .all()
    )

    related_by_type_grouped = {
        atype.name: [art for art in related_by_type if atype in art.article_types]
        for atype in article.article_types
    }

    # Fetch related articles by source
    related_by_source = Article.query.filter(
        Article.source == article.source, Article.id != article.id
    ).all()
    related_by_source_grouped = {
        k: list(g)
        for k, g in groupby(
            sorted(related_by_source, key=lambda x: x.source), key=lambda x: x.source
        )
    }

    # Related articles by country with handling for multiple countries
    related_by_country_dict = {}
    if article.country:
        countries = article.country.split(", ")
        for country in countries:
            related_articles = Article.query.filter(
                Article.country.like(f"%{country}%"), Article.id != article.id
            ).all()
            if country not in related_by_country_dict:
                related_by_country_dict[country] = []
            related_by_country_dict[country].extend(related_articles)

    # Collect all articles to determine top scopes
    all_articles = Article.query.all()
    counter = Counter()
    for a in all_articles:
        if a.article_types:
            for atype in a.article_types:
                counter[("type", atype.name)] += 1
        if a.country:
            for c in a.country.split(", "):
                counter[("country", c)] += 1
        if a.source:
            counter[("source", a.source)] += 1

    # Check if the article is pending approval
    if article.pending_approval:
        # If the article is pending, only allow access to admins
        if not current_user.is_authenticated or not current_user.is_admin:
            flash(
                "⛔️ Nuh uh uh, you didn't say the magic word...",
                "warning",
            )
            return redirect(url_for("home"))

    # Get the top 5 scopes
    top_scopes = counter.most_common(5)
    all_scopes = [{"type": scope[0][0], "name": scope[0][1]} for scope in top_scopes]

    show_team_link = User.query.filter_by(include_in_team_page=True).first() is not None

    return render_template(
        "article.html",
        article=article,
        content_html=content_html,
        related_by_type_grouped=related_by_type_grouped,
        related_by_source_grouped=related_by_source_grouped,
        related_by_country_grouped=related_by_country_dict,
        all_scopes=all_scopes,
        show_team_link=show_team_link,
    )


@app.route("/edit/<slug>", methods=["GET", "POST"])
@login_required
def edit_article(slug):
    app.logger.info(f"Editing article with slug: {slug}")

    article = Article.query.filter_by(slug=slug).first_or_404()
    if not article:
        app.logger.warning(f"Article with slug {slug} not found")
        flash("Article not found.")
        return redirect(url_for("home"))

    # If the article is pending approval, restrict editing to admins
    if article.pending_approval and not current_user.is_admin:
        flash("⛔️ This article is pending approval and cannot be edited.", "warning")
        return redirect(url_for("home"))

    categories = Category.query.all()
    countries = [country.name for country in pycountry.countries]
    all_article_types = ArticleType.query.all()  # Fetch all article types

    if not (current_user.username == article.author or current_user.is_admin):
        app.logger.warning(
            f"Unauthorized edit attempt by user {current_user.username} on article {slug}"
        )
        flash("⛔️ You do not have permission to edit this article.")
        return redirect(url_for("home"))

    if request.method == "POST":
        app.logger.info(f"Processing POST request for editing article {slug}")

        try:
            original_title = article.title
            article.title = request.form["title"]
            article.content = request.form["content"]
            article.country = ", ".join(request.form.getlist("countries"))

            # Handle article types
            selected_article_type_ids = request.form.getlist("article_types")
            selected_article_types = ArticleType.query.filter(
                ArticleType.id.in_(selected_article_type_ids)
            ).all()
            article.article_types = selected_article_types

            # Update DL links
            article.download_link = request.form["download_link"]
            article.download_link2 = request.form.get("download_link2")
            article.download_link3 = request.form.get("download_link3")

            # Update magnet links
            article.magnet_link = request.form.get("magnet_link")
            article.magnet_link2 = request.form.get("magnet_link2")
            article.magnet_link3 = request.form.get("magnet_link3")

            # Update torrent links
            article.torrent_link = request.form.get("torrent_link")
            article.torrent_link2 = request.form.get("torrent_link2")
            article.torrent_link3 = request.form.get("torrent_link3")

            # Update IPFS links
            article.ipfs_link = request.form.get("ipfs_link")
            article.ipfs_link2 = request.form.get("ipfs_link2")
            article.ipfs_link3 = request.form.get("ipfs_link3")

            # Update external collaboration links
            article.external_collaboration = request.form.get("external_collaboration")
            article.external_collaboration2 = request.form.get(
                "external_collaboration2"
            )
            article.external_collaboration3 = request.form.get(
                "external_collaboration3"
            )

            article.download_size = request.form["download_size"]
            article.source = request.form.get("source", "")

            # Extract and handle the publication and last edited dates
            publish_date_str = request.form.get("publish_date")
            if publish_date_str:
                article.publish_date = datetime.strptime(
                    publish_date_str, "%Y-%m-%dT%H:%M"
                )

            last_edited_str = request.form.get("last_edited")
            if last_edited_str:
                article.last_edited = datetime.strptime(
                    last_edited_str, "%Y-%m-%dT%H:%M"
                )

            if original_title != article.title:
                article.slug = slugify(article.title)
                # Ensure unique slug
                original_slug = article.slug
                count = 1
                while Article.query.filter(
                    Article.slug == article.slug, Article.id != article.id
                ).first():
                    article.slug = f"{original_slug}-{count}"
                    count += 1

            # Handle categories
            selected_category_ids = request.form.getlist("categories")
            selected_categories = Category.query.filter(
                Category.id.in_(selected_category_ids)
            ).all()
            article.categories = selected_categories

            db.session.commit()
            app.logger.info(f"Article {slug} updated successfully")
            flash("👍 Article updated successfully.")
            return redirect(url_for("article", slug=article.slug))

        except Exception as e:
            app.logger.error(f"Error updating article {slug}: {e}", exc_info=True)
            flash("Error updating article.")
            return redirect(url_for("edit_article", slug=slug))

    else:
        selected_countries = article.country.split(", ") if article.country else []
        selected_categories = [category.id for category in article.categories]
        selected_article_type_ids = [atype.id for atype in article.article_types]

        return render_template(
            "edit_article.html",
            article=article,
            categories=categories,
            countries=countries,
            selected_countries=selected_countries,
            all_article_types=all_article_types,
            selected_article_type_ids=selected_article_type_ids,
            selected_categories=selected_categories,
        )


@app.route("/source/<source>")
def articles_by_source(source):
    articles = Article.query.filter_by(source=source).all()
    article_count = len(articles)  # Get the count of articles

    # Collect all articles to determine top scopes
    all_articles = Article.query.all()
    counter = Counter()
    for article in all_articles:
        if article.article_type:
            counter[("type", article.article_type)] += 1
        if article.country:
            for country in article.country.split(", "):
                counter[("country", country)] += 1
        if article.source:
            counter[("source", article.source)] += 1

    # Get the top 5 scopes
    top_scopes = counter.most_common(5)
    all_scopes = [{"type": scope[0][0], "name": scope[0][1]} for scope in top_scopes]
    show_team_link = User.query.filter_by(include_in_team_page=True).first() is not None

    return render_template(
        "source_articles.html",
        articles=articles,
        source=source,
        article_count=article_count,
        all_scopes=all_scopes,
        show_team_link=show_team_link,
    )


@app.route("/country/<country>")
def articles_by_country(country):
    articles = Article.query.filter(Article.country.like(f"%{country}%")).all()
    article_count = len(articles)  # Get the count of articles

    # Collect all articles to determine top scopes
    all_articles = Article.query.all()
    counter = Counter()
    for article in all_articles:
        if article.article_type:
            counter[("type", article.article_type)] += 1
        if article.country:
            for c in article.country.split(", "):
                counter[("country", c)] += 1
        if article.source:
            counter[("source", article.source)] += 1

    # Get the top 5 scopes
    top_scopes = counter.most_common(5)
    all_scopes = [{"type": scope[0][0], "name": scope[0][1]} for scope in top_scopes]
    show_team_link = User.query.filter_by(include_in_team_page=True).first() is not None

    return render_template(
        "country_articles.html",
        articles=articles,
        country=country,
        article_count=article_count,
        all_scopes=all_scopes,
        show_team_link=show_team_link,
    )


@app.route("/author/<author>")
def articles_by_author(author):
    articles = Article.query.filter_by(author=author).all()
    article_count = len(articles)  # Get the count of articles

    # Collect all articles to determine top scopes
    all_articles = Article.query.all()
    counter = Counter()
    for article in all_articles:
        if article.article_type:
            counter[("type", article.article_type)] += 1
        if article.country:
            for c in article.country.split(", "):
                counter[("country", c)] += 1
        if article.source:
            counter[("source", article.source)] += 1

    # Get the top 5 scopes
    top_scopes = counter.most_common(5)
    all_scopes = [{"type": scope[0][0], "name": scope[0][1]} for scope in top_scopes]
    show_team_link = User.query.filter_by(include_in_team_page=True).first() is not None

    return render_template(
        "author_articles.html",
        articles=articles,
        author=author,
        article_count=article_count,
        all_scopes=all_scopes,
        show_team_link=show_team_link,
    )


@app.route("/type/<article_type>")
def articles_by_type(article_type):
    # Fetch the specific article type
    type_obj = ArticleType.query.filter_by(name=article_type).first()

    if article_type.lower() == "all":
        articles = Article.query.all()
    elif type_obj:
        # Use the relationship to filter articles
        articles = type_obj.articles
    else:
        # Handle case where no such type exists
        articles = []

    article_count = len(articles)  # Get the count of articles

    # Collect all articles to determine top scopes
    all_articles = Article.query.all()
    counter = Counter()
    for article in all_articles:
        for atype in article.article_types:
            counter[("type", atype.name)] += 1
        if article.country:
            for c in article.country.split(", "):
                counter[("country", c)] += 1
        if article.source:
            counter[("source", article.source)] += 1

    # Get the top 5 scopes
    top_scopes = counter.most_common(5)
    all_scopes = [{"type": scope[0][0], "name": scope[0][1]} for scope in top_scopes]
    show_team_link = User.query.filter_by(include_in_team_page=True).first() is not None

    return render_template(
        "type_articles.html",
        articles=articles,
        article_type=article_type,
        article_count=article_count,
        all_scopes=all_scopes,
        show_team_link=show_team_link,
    )


@app.route("/all_categories")
def all_categories():
    # Fetch all article types that have at least one article
    article_types = (
        ArticleType.query.filter(ArticleType.articles.any())
        .order_by(ArticleType.name)
        .all()
    )

    # Fetch countries and sources from articles
    articles = Article.query.all()
    countries = sorted(
        set(
            country
            for article in articles
            for country in article.country.split(", ")
            if article.country
        )
    )
    sources = sorted(set(article.source for article in articles if article.source))

    # Collect all articles to determine top scopes
    counter = Counter()
    for article in articles:
        for atype in article.article_types:
            counter[("type", atype.name)] += 1
        if article.country:
            for country in article.country.split(", "):
                counter[("country", country)] += 1
        if article.source:
            counter[("source", article.source)] += 1

    # Get the top 5 scopes
    top_scopes = counter.most_common(5)
    all_scopes = [{"type": scope[0][0], "name": scope[0][1]} for scope in top_scopes]
    show_team_link = User.query.filter_by(include_in_team_page=True).first() is not None

    return render_template(
        "all_categories.html",
        article_types=article_types,
        countries=countries,
        sources=sources,
        all_scopes=all_scopes,
        show_team_link=show_team_link,
    )


@app.route("/delete_article/<int:article_id>", methods=["POST"])
@login_required
def delete_article(article_id):
    article = Article.query.get_or_404(article_id)

    # Check if the current user is the author or an admin
    if not (current_user.username == article.author or current_user.is_admin):
        flash("⛔️ You do not have permission to delete this article.")
        return redirect(url_for("home"))

    db.session.delete(article)
    db.session.commit()
    flash("🗑️ Article deleted successfully.")
    return redirect(url_for("home"))


@app.route("/settings", methods=["GET", "POST"])
@login_required
def user_settings():
    bio_form = BioForm(obj=current_user)
    password_form = PasswordForm()
    team_page_form = TeamPageForm(obj=current_user)
    display_name_form = DisplayNameForm(obj=current_user)
    custom_url_form = CustomUrlForm(obj=current_user)
    avatar_form = AvatarForm()

    if "submit_bio" in request.form and bio_form.validate_on_submit():
        current_user.bio = bio_form.bio.data
        db.session.commit()
        flash("Your bio has been updated.", "success")

    elif "submit_password" in request.form and password_form.validate_on_submit():
        if current_user.check_password(password_form.current_password.data):
            current_user.set_password(password_form.new_password.data)
            db.session.commit()
            flash("Your password has been updated. Please log in again.", "success")
            logout_user()
            return redirect(url_for("login"))
        else:
            flash("Current password is incorrect.", "danger")

    elif "submit_team" in request.form and team_page_form.validate_on_submit():
        current_user.include_in_team_page = team_page_form.include_in_team_page.data
        db.session.commit()
        flash("Team page settings updated", "success")

    elif (
        "submit_display_name" in request.form and display_name_form.validate_on_submit()
    ):
        current_user.display_name = display_name_form.display_name.data
        db.session.commit()
        flash("Your display name has been updated.", "success")

    elif "submit_custom_url" in request.form and custom_url_form.validate_on_submit():
        current_user.custom_url = custom_url_form.custom_url.data
        db.session.commit()
        flash("Your custom URL has been updated.", "success")

    elif avatar_form.validate_on_submit() and "avatar" in request.files:
        file = avatar_form.avatar.data
        filename = secure_filename(file.filename)
        if filename != "":
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            current_user.avatar = filename
            db.session.commit()
            flash("Your avatar has been updated.", "success")
        else:
            flash("No file selected.", "warning")

    return render_template(
        "settings.html",
        bio_form=bio_form,
        password_form=password_form,
        team_page_form=team_page_form,
        display_name_form=display_name_form,
        custom_url_form=custom_url_form,
        avatar_form=avatar_form,
    )


@app.route("/update_bio", methods=["POST"])
@login_required
def update_bio():
    form = UserSettingsForm()
    user = current_user

    if form.validate_on_submit():
        user.bio = form.bio.data
        db.session.commit()
        flash("👍 Your bio has been updated.", "success")
    else:
        flash("Error updating bio.", "danger")

    return redirect(url_for("user_settings"))


@app.route("/change_password", methods=["POST"])
@login_required
def change_password():
    form = UserSettingsForm()
    user = current_user

    if form.validate_on_submit():
        if user.check_password(form.current_password.data):
            user.set_password(form.new_password.data)
            db.session.commit()
            flash("👍 Your password has been updated.", "success")
            logout_user()
            return redirect(url_for("login"))
        else:
            flash("⛔️ Current password is incorrect.", "danger")

    return redirect(url_for("user_settings"))


@app.route("/all_articles/<category>")
def all_articles(category):
    articles = []
    title = ""
    article_count = 0  # Initialize the article count

    if category == "recent":
        articles = (
            Article.query.filter_by(pending_approval=False)
            .order_by(Article.publish_date.desc())
            .all()
        )
        title = "All Recently Published Articles"
    elif category == "edited":
        articles = (
            Article.query.filter(
                Article.pending_approval == False, Article.last_edited != None
            )
            .order_by(Article.last_edited.desc())
            .all()
        )
        title = "All Recently Edited Articles"
    elif category == "external":
        articles = (
            Article.query.filter(
                Article.pending_approval == False,
                Article.external_collaboration != None,
                Article.external_collaboration != "",
            )
            .order_by(Article.publish_date.desc())
            .all()
        )
        title = "All External Collaboration Articles"

    article_count = len(articles)  # Update the article count based on filtered results

    # Collect all articles to determine top scopes
    all_articles = Article.query.filter_by(pending_approval=False).all()
    counter = Counter()
    for article in all_articles:
        if article.article_type:
            counter[("type", article.article_type)] += 1
        if article.country:
            for country in article.country.split(", "):
                counter[("country", country)] += 1
        if article.source:
            counter[("source", article.source)] += 1

    # Get the top 5 scopes
    top_scopes = counter.most_common(5)
    all_scopes = [{"type": scope[0][0], "name": scope[0][1]} for scope in top_scopes]
    show_team_link = User.query.filter_by(include_in_team_page=True).first() is not None

    return render_template(
        "all_articles.html",
        articles=articles,
        article_count=article_count,
        title=title,
        all_scopes=all_scopes,
        show_team_link=show_team_link,
    )


@app.route("/team")
def team():
    users = User.query.filter(User.include_in_team_page).all()
    return render_template("team.html", users=users)


# Error handler
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error("An error occurred: %s", e)
    return "An internal error occurred", 500


def initialize_article_types():
    existing_types = [atype.name for atype in ArticleType.query.all()]
    for atype in [
        "Banker's Box",
        "Corporate",
        "Cyberwar",
        "Hack",
        "Leak",
        "News",
        "Opinion",
        "Other",
        "Ransomware",
        "Research",
        "Scrape",
    ]:
        if atype not in existing_types:
            new_type = ArticleType(name=atype)
            db.session.add(new_type)
    db.session.commit()


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


# Database initialization function
def initialize_database():
    with app.app_context():
        db.create_all()
        initialize_article_types()  # Initialize article types after creating all tables


# Call the database initialization function
initialize_database()


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True, host="0.0.0.0", port=5000)
