"""add unique constraint on aggregated_data (dashboard_id, graph_id, dims)

Revision ID: 91f5436a3098
Revises: f50a4054569c
Create Date: 2026-05-07 20:35:07.146278

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91f5436a3098'
down_revision: Union[str, Sequence[str], None] = 'f50a4054569c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(
        "uq_aggregated_data_dashboard_graph_dims",
        "aggregated_data",
        ["dashboard_id", "graph_id", "dims"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "uq_aggregated_data_dashboard_graph_dims",
        "aggregated_data",
        type_="unique",
    )
