# Create this manually if needed: alembic/versions/create_initial_tables.py

"""Create initial tables

Revision ID: create_initial_001
Revises:
Create Date: 2024-XX-XX XX:XX:XX.XXXXXX

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "create_initial_001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    # Create category table
    op.create_table(
        "category",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("type", sa.Enum("Income", "Expense", name="type"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_category_type"), "category", ["type"], unique=False)

    # Create transactions table
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("type", sa.Enum("Income", "Expense", name="type"), nullable=False),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["category.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("transactions")
    op.drop_index(op.f("ix_category_type"), table_name="category")
    op.drop_table("category")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_table("users")
