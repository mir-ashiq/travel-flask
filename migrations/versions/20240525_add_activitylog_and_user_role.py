"""
Alembic migration for ActivityLog model and User.role field
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240525_add_activitylog_and_user_role'
down_revision = 'f0320f918c6b'  # Set this to the latest previous migration revision
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'activity_log',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id')),
        sa.Column('username', sa.String(64)),
        sa.Column('action', sa.String(256)),
        sa.Column('timestamp', sa.DateTime, nullable=False)
    )
    op.add_column('user', sa.Column('role', sa.String(32), server_default='admin'))

def downgrade():
    op.drop_column('user', 'role')
    op.drop_table('activity_log')
