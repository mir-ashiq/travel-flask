"""
Add custom_destinations field to TourPackage
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240525_add_custom_destinations_to_tourpackage'
down_revision = '20240525_add_itineraryday_model'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('tour_package', sa.Column('custom_destinations', sa.String(length=500)))

def downgrade():
    op.drop_column('tour_package', 'custom_destinations')
