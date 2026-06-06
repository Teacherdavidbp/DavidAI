"""SOS Alert MVP Phase 1 — indexes and status constraint.

Revision ID: 004_sos_alerts
Revises: 003_trusted_contacts
Create Date: 2026-06-05

Note: sos_alerts table was created in 001_initial_schema. This migration
aligns the schema for Phase 1 MVP queries (active vs resolved alerts).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_sos_alerts"
down_revision: Union[str, None] = "003_trusted_contacts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_sos_alerts_user_status",
        "sos_alerts",
        ["user_id", "status"],
        unique=False,
    )
    op.create_check_constraint(
        "ck_sos_alerts_status",
        "sos_alerts",
        "status IN ('active', 'resolved')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_sos_alerts_status", "sos_alerts", type_="check")
    op.drop_index("ix_sos_alerts_user_status", table_name="sos_alerts")
