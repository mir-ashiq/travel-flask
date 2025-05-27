"""
Add published column to tour_package table (NO-OP: column already exists)
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240526_add_published_to_tourpackage'
down_revision = 'd121900410b6'
branch_labels = None
depends_on = None

def upgrade():
    # Column already exists, so do nothing
    pass

def downgrade():
    # Only drop if exists
    with op.batch_alter_table('tour_package') as batch_op:
        try:
            batch_op.drop_column('published')
        except Exception:
            pass
