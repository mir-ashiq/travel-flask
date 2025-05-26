"""
Add advanced fields to TourPackage: itinerary, accommodations, included, excluded
"""
from alembic import op
import sqlalchemy as sa

revision = '20240525_add_advanced_fields_to_tourpackage'
down_revision = '6320f3ef98ca'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('tour_package', sa.Column('itinerary', sa.Text(), nullable=True))
    op.add_column('tour_package', sa.Column('accommodations', sa.Text(), nullable=True))
    op.add_column('tour_package', sa.Column('included', sa.Text(), nullable=True))
    op.add_column('tour_package', sa.Column('excluded', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('tour_package', 'itinerary')
    op.drop_column('tour_package', 'accommodations')
    op.drop_column('tour_package', 'included')
    op.drop_column('tour_package', 'excluded')
