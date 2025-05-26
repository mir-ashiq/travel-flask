"""
Add ItineraryDay model for advanced itinerary structuring
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240525_add_itineraryday_model'
down_revision = '20240525_add_advanced_fields_to_tourpackage'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'itinerary_day',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('package_id', sa.Integer(), sa.ForeignKey('tour_package.id'), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
    )

def downgrade():
    op.drop_table('itinerary_day')
