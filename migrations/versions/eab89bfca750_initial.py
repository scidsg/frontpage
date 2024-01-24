"""initial

Revision ID: eab89bfca750
Revises:
Create Date: 2024-01-24 09:10:15.553158
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "eab89bfca750"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "article",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("author", sa.String(length=50), nullable=False),
        sa.Column("publish_date", sa.DateTime(), nullable=True),
        sa.Column("country", sa.String(length=50), nullable=True),
        sa.Column("download_link", sa.String(length=255), nullable=True),
        sa.Column("download_link2", sa.String(length=255), nullable=True),
        sa.Column("download_link3", sa.String(length=255), nullable=True),
        sa.Column("magnet_link", sa.String(length=255), nullable=True),
        sa.Column("magnet_link2", sa.String(length=255), nullable=True),
        sa.Column("magnet_link3", sa.String(length=255), nullable=True),
        sa.Column("torrent_link", sa.String(length=255), nullable=True),
        sa.Column("torrent_link2", sa.String(length=255), nullable=True),
        sa.Column("torrent_link3", sa.String(length=255), nullable=True),
        sa.Column("ipfs_link", sa.String(length=255), nullable=True),
        sa.Column("ipfs_link2", sa.String(length=255), nullable=True),
        sa.Column("ipfs_link3", sa.String(length=255), nullable=True),
        sa.Column("download_size", sa.String(length=255), nullable=True),
        sa.Column("external_collaboration", sa.String(length=255), nullable=True),
        sa.Column("external_collaboration2", sa.String(length=255), nullable=True),
        sa.Column("external_collaboration3", sa.String(length=255), nullable=True),
        sa.Column("article_type", sa.String(length=50), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("last_edited", sa.DateTime(), nullable=True),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("pending_approval", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "article_type",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "category",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "invitation_code",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False),
        sa.Column("expiration_date", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=True),
        sa.Column("password_hash", sa.String(length=100), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("include_in_team_page", sa.Boolean(), nullable=True),
        sa.Column("display_name", sa.String(length=100), nullable=True),
        sa.Column("custom_url", sa.String(length=255), nullable=True),
        sa.Column("avatar", sa.String(length=255), nullable=True),
        sa.Column("requires_approval", sa.Boolean(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )

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


def downgrade():
    op.drop_table("article_categories")
    op.drop_table("article_article_types")
    op.drop_table("user")
    op.drop_table("invitation_code")
    op.drop_table("category")
    op.drop_table("article_type")
    op.drop_table("article")
