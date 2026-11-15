"""add Jira fields to incidents

Revision ID: c4a91b2d7e10
Revises: 91f1335e56ef
Create Date: 2026-11-15

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4a91b2d7e10"
down_revision: Union[str, Sequence[str], None] = "91f1335e56ef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "incidents",
        sa.Column("jira_issue_key", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "incidents",
        sa.Column("jira_issue_url", sa.Text(), nullable=True),
    )
    op.add_column(
        "incidents",
        sa.Column(
            "jira_sync_status",
            sa.String(length=20),
            server_default="NOT_REQUESTED",
            nullable=False,
        ),
    )
    op.add_column(
        "incidents",
        sa.Column("jira_last_error", sa.Text(), nullable=True),
    )
    op.add_column(
        "incidents",
        sa.Column(
            "jira_synced_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
    )
    op.create_unique_constraint(
        "uq_incidents_jira_issue_key",
        "incidents",
        ["jira_issue_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_incidents_jira_issue_key",
        "incidents",
        type_="unique",
    )
    op.drop_column("incidents", "jira_synced_at")
    op.drop_column("incidents", "jira_last_error")
    op.drop_column("incidents", "jira_sync_status")
    op.drop_column("incidents", "jira_issue_url")
    op.drop_column("incidents", "jira_issue_key")
