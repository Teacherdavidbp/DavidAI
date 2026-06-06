"""Add provider metadata to sos_notifications for Twilio delivery tracking.

Revision ID: 006_sos_notification_provider
Revises: 005_sos_notifications
Create Date: 2026-06-06

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_sos_notification_provider"
down_revision: Union[str, None] = "005_sos_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sos_notifications",
        sa.Column("provider_sid", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "sos_notifications",
        sa.Column("provider_detail", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sos_notifications", "provider_detail")
    op.drop_column("sos_notifications", "provider_sid")
