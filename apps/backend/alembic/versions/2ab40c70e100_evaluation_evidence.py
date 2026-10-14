"""Allow unavailable recall and record evaluation provenance."""

from alembic import op
import sqlalchemy as sa

revision = "2ab40c70e100"
down_revision = "18ffd4e296d9"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("evaluation_results") as batch:
        batch.alter_column(
            "context_recall", existing_type=sa.Numeric(5, 4), nullable=True
        )
        batch.add_column(sa.Column("details", sa.JSON(), nullable=True))


def downgrade():
    op.execute(
        "UPDATE evaluation_results SET context_recall = 0 WHERE context_recall IS NULL"
    )
    with op.batch_alter_table("evaluation_results") as batch:
        batch.drop_column("details")
        batch.alter_column(
            "context_recall", existing_type=sa.Numeric(5, 4), nullable=False
        )
