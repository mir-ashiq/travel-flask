"""merge activitylog/user_role and custom_destinations heads

Revision ID: 1efcc6474e60
Revises: 20240525_add_activitylog_and_user_role, 20240525_add_custom_destinations_to_tourpackage
Create Date: 2025-05-25 14:03:41.731822

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1efcc6474e60'
down_revision = ('20240525_add_activitylog_and_user_role', '20240525_add_custom_destinations_to_tourpackage')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
