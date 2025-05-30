"""
Alembic migration script to add hero_bg_image and hero_slides fields to SiteSettings.

Revision ID: 20240528_add_hero_bg_image_and_slides_to_sitesettings
Revises: 20240528_add_hero_title_subtitle_to_sitesettings
Create Date: 2025-05-28
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240528_add_hero_bg_image_and_slides_to_sitesettings'
down_revision = '20240528_add_hero_title_subtitle_to_sitesettings'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('site_settings', sa.Column('hero_bg_image', sa.String(length=200), nullable=True))
    op.add_column('site_settings', sa.Column('hero_slides', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('site_settings', 'hero_bg_image')
    op.drop_column('site_settings', 'hero_slides')
