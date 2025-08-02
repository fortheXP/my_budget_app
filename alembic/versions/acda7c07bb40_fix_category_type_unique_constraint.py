from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from typing import Union, Sequence

# revision identifiers, used by Alembic.
revision: str = "acda7c07bb40"
down_revision: Union[str, Sequence[str], None] = "create_initial_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop constraints and index first
    op.drop_constraint(op.f("category_type_key"), "category", type_="unique")
    op.drop_index(op.f("ix_category_type"), table_name="category")

    # Create the enum type
    type_enum = postgresql.ENUM("Income", "Expense", name="type")
    type_enum.create(op.get_bind())

    # Convert column type using raw SQL with USING clause
    op.execute("""
        ALTER TABLE category 
        ALTER COLUMN type TYPE type 
        USING CASE 
            WHEN type = 'Income' THEN 'Income'::type
            WHEN type = 'Expense' THEN 'Expense'::type
            ELSE 'Expense'::type
        END
    """)

    # Set column to not nullable
    op.alter_column("category", "type", nullable=False)

    # Create new index (non-unique)
    op.create_index(op.f("ix_category_type"), "category", ["type"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the index
    op.drop_index(op.f("ix_category_type"), table_name="category")

    # Convert back to VARCHAR
    op.alter_column(
        "category",
        "type",
        existing_type=postgresql.ENUM("Income", "Expense", name="type"),
        type_=sa.VARCHAR(),
        nullable=True,
    )

    # Drop the enum type
    postgresql.ENUM(name="type").drop(op.get_bind())

    # Recreate original constraints and index
    op.create_index(op.f("ix_category_type"), "category", ["type"], unique=True)
    op.create_unique_constraint(
        op.f("category_type_key"),
        "category",
        ["type"],
        postgresql_nulls_not_distinct=False,
    )
