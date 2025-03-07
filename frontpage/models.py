from flask_login import UserMixin
from slugify import slugify
from sqlalchemy import text
from werkzeug.security import check_password_hash

from .crypto import pwd_context
from .db import db

# Association table for articles and article types
article_article_types = db.Table(
    "article_article_types",
    db.Column("article_id", db.Integer, db.ForeignKey("articles.id"), primary_key=True),
    db.Column(
        "article_type_id",
        db.Integer,
        db.ForeignKey("article_types.id"),
        primary_key=True,
    ),
    sqlite_with_rowid=False,
)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)
    include_in_team_page = db.Column(db.Boolean, server_default=text("FALSE"))
    display_name = db.Column(db.String(100))
    custom_url = db.Column(db.String(255))
    avatar = db.Column(db.String(255))
    requires_approval = db.Column(db.Boolean, server_default=text("FALSE"), nullable=False)
    is_admin = db.Column(db.Boolean, server_default=text("FALSE"), nullable=False)

    def set_password(self, password):
        self.password_hash = pwd_context.hash(password)

    def check_password(self, password):
        try:
            # First, try to verify the password with Passlib
            return pwd_context.verify(password, self.password_hash)
        except ValueError:
            # If it fails (old hash), fall back to Werkzeug's method
            return check_password_hash(self.password_hash, password)


class Logo(db.Model):
    __tablename__ = "logos"

    id = db.Column(db.Integer, primary_key=True)
    file = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Logo {self.file}>"


class Citation(db.Model):
    __tablename__ = "citations"

    id = db.Column(db.Integer, primary_key=True)
    article = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Citation {self.article}>"


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

    def __repr__(self):
        return "<Category %r>" % self.name


# Association table for the many-to-many relationship
article_categories = db.Table(
    "article_categories",
    db.Column("article_id", db.Integer, db.ForeignKey("articles.id"), primary_key=True),
    db.Column("category_id", db.Integer, db.ForeignKey("categories.id"), primary_key=True),
    sqlite_with_rowid=False,
)


class Article(db.Model):
    __tablename__ = "articles"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(50), nullable=False)
    publish_date = db.Column(db.DateTime, nullable=False)
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
    source = db.Column(db.String(255))
    last_edited = db.Column(db.DateTime)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    pending_approval = db.Column(db.Boolean, server_default=text("FALSE"), nullable=False)
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
    __tablename__ = "article_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

    def __repr__(self):
        return "<ArticleType %r>" % self.name


class InvitationCode(db.Model):
    __tablename__ = "invitation_codes"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False, unique=True)
    used = db.Column(db.Boolean, server_default=text("FALSE"), nullable=False)
    expiration_date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"<InvitationCode {self.code}>"
