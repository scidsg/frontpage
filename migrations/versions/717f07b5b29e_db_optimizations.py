"""db optimizations combined with new tables integration

Revision ID: 717f07b5b29e
Revises: eab89bfca750
Create Date: 2024-01-24 12:46:49.419776
"""

from contextlib import contextmanager

import sqlalchemy as sa
from alembic import op

revision = "717f07b5b29e"
down_revision = "eab89bfca750"
branch_labels = None
depends_on = None

article_cols = (
    "id, title, content, author, publish_date, country, download_link, download_link2, "
    "download_link3, magnet_link, magnet_link2, magnet_link3, torrent_link, torrent_link2, "
    "torrent_link3, ipfs_link, ipfs_link2, ipfs_link3, download_size, external_collaboration, "
    "external_collaboration2, external_collaboration3, source, last_edited, slug, pending_approval"
)


@contextmanager
def transfer(new: str, old: str | None = None, cols: str | None = None) -> None:
    if not old:
        op.execute(f"ALTER TABLE {new} RENAME TO {new}_old")
        old = f"{new}_old"
    yield
    if not cols:
        cols = "*"
    op.execute(f"INSERT INTO {new} SELECT {cols} FROM {old}")


def upgrade() -> None:
    # Create and transfer to new 'article_types' table
    with transfer("article_types", "article_type"):
        op.create_table(
            "article_types",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=50), nullable=False),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_article_types")),
            sa.UniqueConstraint("name", name=op.f("uq_article_types_name")),
        )

    # Create and transfer to new 'articles' table
    with transfer("article", "articles", cols=article_cols + ", 0 AS pending_approval"):
        op.create_table(
            "article",
            sa.Column("id", sa.INTEGER(), nullable=False),
            sa.Column("title", sa.VARCHAR(length=100), nullable=False),
            sa.Column("content", sa.TEXT(), nullable=False),
            sa.Column("author", sa.VARCHAR(length=50), nullable=False),
            sa.Column("publish_date", sa.DATETIME(), nullable=True),
            sa.Column("country", sa.VARCHAR(length=50), nullable=True),
            sa.Column("download_link", sa.VARCHAR(length=255), nullable=True),
            sa.Column("download_link2", sa.VARCHAR(length=255), nullable=True),
            sa.Column("download_link3", sa.VARCHAR(length=255), nullable=True),
            sa.Column("magnet_link", sa.VARCHAR(length=255), nullable=True),
            sa.Column("magnet_link2", sa.VARCHAR(length=255), nullable=True),
            sa.Column("magnet_link3", sa.VARCHAR(length=255), nullable=True),
            sa.Column("torrent_link", sa.VARCHAR(length=255), nullable=True),
            sa.Column("torrent_link2", sa.VARCHAR(length=255), nullable=True),
            sa.Column("torrent_link3", sa.VARCHAR(length=255), nullable=True),
            sa.Column("ipfs_link", sa.VARCHAR(length=255), nullable=True),
            sa.Column("ipfs_link2", sa.VARCHAR(length=255), nullable=True),
            sa.Column("ipfs_link3", sa.VARCHAR(length=255), nullable=True),
            sa.Column("download_size", sa.VARCHAR(length=255), nullable=True),
            sa.Column("external_collaboration", sa.VARCHAR(length=255), nullable=True),
            sa.Column("external_collaboration2", sa.VARCHAR(length=255), nullable=True),
            sa.Column("external_collaboration3", sa.VARCHAR(length=255), nullable=True),
            sa.Column("article_type", sa.VARCHAR(length=50), nullable=True),
            sa.Column("source", sa.VARCHAR(length=255), nullable=True),
            sa.Column("last_edited", sa.DATETIME(), nullable=True),
            sa.Column("slug", sa.VARCHAR(length=255), nullable=False),
            sa.Column("pending_approval", sa.BOOLEAN(), nullable=False, server_default="0"),
            sa.PrimaryKeyConstraint("id", name="pk_article"),
            sa.UniqueConstraint("slug", name="uq_article_slug"),
        )

    # New table definitions as per the latest migration file `969132890ea8_.py`
    op.create_table(
        "citations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("article", sa.String(length=255), nullable=False),
        sa.Column("link", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_citations")),
    )
    op.create_table(
        "logos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("file", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_logos")),
    )
    with transfer("categories", "category"):
        op.create_table(
            "categories",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=50), nullable=False),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
            sa.UniqueConstraint("name", name=op.f("uq_categories_name")),
        )

    with transfer("invitation_codes", "invitation_code"):
        op.create_table(
            "invitation_codes",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("code", sa.String(length=50), nullable=False),
            sa.Column("used", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False),
            sa.Column("expiration_date", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_invitation_codes")),
            sa.UniqueConstraint("code", name=op.f("uq_invitation_codes_code")),
        )

    with transfer("users", "user"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("username", sa.String(length=100), nullable=False),
            sa.Column("password_hash", sa.String(length=100), nullable=False),
            sa.Column("bio", sa.Text(), nullable=True),
            sa.Column(
                "include_in_team_page",
                sa.Boolean(),
                server_default=sa.text("FALSE"),
                nullable=True,
            ),
            sa.Column("display_name", sa.String(length=100), nullable=True),
            sa.Column("custom_url", sa.String(length=255), nullable=True),
            sa.Column("avatar", sa.String(length=255), nullable=True),
            sa.Column(
                "requires_approval", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False
            ),
            sa.Column("is_admin", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
            sa.UniqueConstraint("username", name=op.f("uq_users_username")),
        )

    with transfer("article_article_types"):
        op.create_table(
            "article_article_types",
            sa.Column("article_id", sa.Integer(), nullable=False),
            sa.Column("article_type_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(
                ["article_id"],
                ["articles.id"],
                name=op.f("fk_article_article_types_article_type_id_article_types"),
            ),
            sa.ForeignKeyConstraint(
                ["article_type_id"],
                ["article_types.id"],
                name=op.f("fk_article_article_types_article_id_articles"),
            ),
            sa.PrimaryKeyConstraint(
                "article_id", "article_type_id", name=op.f("pk_article_article_types")
            ),
            sqlite_with_rowid=False,
        )

    with transfer("article_categories"):
        op.create_table(
            "article_categories",
            sa.Column("article_id", sa.Integer(), nullable=False),
            sa.Column("category_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(
                ["article_id"],
                ["article.id"],
                name=op.f("fk_article_categories_article_id_articles"),
            ),
            sa.ForeignKeyConstraint(
                ["category_id"],
                ["category.id"],
                name=op.f("fk_article_categories_category_id_categories"),
            ),
            sa.PrimaryKeyConstraint(
                "article_id", "category_id", name=op.f("pk_article_categories")
            ),
            sqlite_with_rowid=False,
        )

    op.drop_table("article_article_types_old")
    op.drop_table("article_categories_old")
    op.drop_table("article")
    op.drop_table("user")
    op.drop_table("article_type")
    op.drop_table("category")
    op.drop_table("invitation_code")


def downgrade() -> None:
    # Explicitly drop tables if they exist before recreating them
    op.execute("DROP TABLE IF EXISTS invitation_code")
    op.execute("DROP TABLE IF EXISTS category")
    op.execute("DROP TABLE IF EXISTS article_type")
    op.execute("DROP TABLE IF EXISTS user")
    op.execute("DROP TABLE IF EXISTS article")
    op.execute("DROP TABLE IF EXISTS article_article_types")
    op.execute("DROP TABLE IF EXISTS article_categories")

    # Recreate the original tables with the original schema
    with transfer("invitation_code", "invitation_codes"):
        op.create_table(
            "invitation_code",
            sa.Column("id", sa.INTEGER(), nullable=False),
            sa.Column("code", sa.VARCHAR(length=50), nullable=False),
            sa.Column("used", sa.BOOLEAN(), nullable=False),
            sa.Column("expiration_date", sa.DATETIME(), nullable=False),
            sa.PrimaryKeyConstraint("id", name="pk_invitation_code"),
            sa.UniqueConstraint("code", name="uq_invitation_code_code"),
        )

    with transfer("category", "categories"):
        op.create_table(
            "category",
            sa.Column("id", sa.INTEGER(), nullable=False),
            sa.Column("name", sa.VARCHAR(length=50), nullable=False),
            sa.PrimaryKeyConstraint("id", name="pk_category"),
            sa.UniqueConstraint("name", name="uq_category_name"),
        )

    with transfer("article_type", "article_types"):
        op.create_table(
            "article_type",
            sa.Column("id", sa.INTEGER(), nullable=False),
            sa.Column("name", sa.VARCHAR(length=50), nullable=False),
            sa.PrimaryKeyConstraint("id", name="pk_article_type"),
            sa.UniqueConstraint("name", name="uq_article_type_name"),
        )

    with transfer("user", "users"):
        op.create_table(
            "user",
            sa.Column("id", sa.INTEGER(), nullable=False),
            sa.Column("username", sa.VARCHAR(length=100), nullable=True),
            sa.Column("password_hash", sa.VARCHAR(length=100), nullable=True),
            sa.Column("bio", sa.TEXT(), nullable=True),
            sa.Column("include_in_team_page", sa.BOOLEAN(), nullable=True),
            sa.Column("display_name", sa.VARCHAR(length=100), nullable=True),
            sa.Column("custom_url", sa.VARCHAR(length=255), nullable=True),
            sa.Column("avatar", sa.VARCHAR(length=255), nullable=True),
            sa.Column("requires_approval", sa.BOOLEAN(), nullable=False),
            sa.Column("is_admin", sa.BOOLEAN(), nullable=False),
            sa.PrimaryKeyConstraint("id", name="pk_user"),
            sa.UniqueConstraint("username", name="uq_user_username"),
        )

    with transfer("article", "articles", cols=article_cols + ", 0 AS pending_approval"):
        op.create_table(
            "article",
            sa.Column("id", sa.INTEGER(), nullable=False),
            sa.Column("title", sa.VARCHAR(length=100), nullable=False),
            sa.Column("content", sa.TEXT(), nullable=False),
            sa.Column("author", sa.VARCHAR(length=50), nullable=False),
            sa.Column("publish_date", sa.DATETIME(), nullable=True),
            sa.Column("country", sa.VARCHAR(length=50), nullable=True),
            sa.Column("download_link", sa.VARCHAR(length=255), nullable=True),
            sa.Column("download_link2", sa.VARCHAR(length=255), nullable=True),
            sa.Column("download_link3", sa.VARCHAR(length=255), nullable=True),
            sa.Column("magnet_link", sa.VARCHAR(length=255), nullable=True),
            sa.Column("magnet_link2", sa.VARCHAR(length=255), nullable=True),
            sa.Column("magnet_link3", sa.VARCHAR(length=255), nullable=True),
            sa.Column("torrent_link", sa.VARCHAR(length=255), nullable=True),
            sa.Column("torrent_link2", sa.VARCHAR(length=255), nullable=True),
            sa.Column("torrent_link3", sa.VARCHAR(length=255), nullable=True),
            sa.Column("ipfs_link", sa.VARCHAR(length=255), nullable=True),
            sa.Column("ipfs_link2", sa.VARCHAR(length=255), nullable=True),
            sa.Column("ipfs_link3", sa.VARCHAR(length=255), nullable=True),
            sa.Column("download_size", sa.VARCHAR(length=255), nullable=True),
            sa.Column("external_collaboration", sa.VARCHAR(length=255), nullable=True),
            sa.Column("external_collaboration2", sa.VARCHAR(length=255), nullable=True),
            sa.Column("external_collaboration3", sa.VARCHAR(length=255), nullable=True),
            sa.Column("article_type", sa.VARCHAR(length=50), nullable=True),
            sa.Column("source", sa.VARCHAR(length=255), nullable=True),
            sa.Column("last_edited", sa.DATETIME(), nullable=True),
            sa.Column("slug", sa.VARCHAR(length=255), nullable=False),
            sa.Column("pending_approval", sa.BOOLEAN(), nullable=False, server_default="0"),
            sa.PrimaryKeyConstraint("id", name="pk_article"),
            sa.UniqueConstraint("slug", name="uq_article_slug"),
        )

    with transfer("article_article_types"):
        op.create_table(
            "article_article_types",
            sa.Column("article_id", sa.Integer(), nullable=False),
            sa.Column("article_type_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(
                ["article_id"],
                ["article.id"],
            ),
            sa.ForeignKeyConstraint(
                ["article_type_id"],
                ["article_type.id"],
            ),
            sa.PrimaryKeyConstraint("article_id", "article_type_id"),
        )

    with transfer("article_categories"):
        op.create_table(
            "article_categories",
            sa.Column("article_id", sa.Integer(), nullable=False),
            sa.Column("category_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(
                ["article_id"],
                ["article.id"],
            ),
            sa.ForeignKeyConstraint(
                ["category_id"],
                ["category.id"],
            ),
            sa.PrimaryKeyConstraint("article_id", "category_id"),
        )

    op.drop_table("article_categories_old")
    op.drop_table("article_article_types_old")
    op.drop_table("users")
    op.drop_table("invitation_codes")
    op.drop_table("categories")
    op.drop_table("articles")
    op.drop_table("article_types")
