"""
Alembic migration script to add hero_title and hero_subtitle fields to SiteSettings.

Revision ID: 20240528_add_hero_title_subtitle_to_sitesettings
Revises: 20240528_add_show_linkedin_youtube_whatsapp_telegram
Create Date: 2025-05-28
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240528_add_hero_title_subtitle_to_sitesettings'
down_revision = '20240528_add_show_linkedin_youtube_whatsapp_telegram'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('site_settings', sa.Column('hero_title', sa.String(length=200), nullable=True))
    op.add_column('site_settings', sa.Column('hero_subtitle', sa.String(length=300), nullable=True))

def downgrade():
    op.drop_column('site_settings', 'hero_title')
    op.drop_column('site_settings', 'hero_subtitle')
