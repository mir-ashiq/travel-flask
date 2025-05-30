"""
Alembic migration script to add show_linkedin, show_youtube, show_whatsapp, and show_telegram fields to SiteSettings.

Revision ID: 20240528_add_show_linkedin_youtube_whatsapp_telegram
Revises: 20240527_add_show_social_to_sitesettings
Create Date: 2025-05-28
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240528_add_show_linkedin_youtube_whatsapp_telegram'
down_revision = '20240527_add_show_social_to_sitesettings'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('site_settings', sa.Column('show_linkedin', sa.Boolean(), nullable=True, server_default=sa.true()))
    op.add_column('site_settings', sa.Column('show_youtube', sa.Boolean(), nullable=True, server_default=sa.true()))
    op.add_column('site_settings', sa.Column('show_whatsapp', sa.Boolean(), nullable=True, server_default=sa.true()))
    op.add_column('site_settings', sa.Column('show_telegram', sa.Boolean(), nullable=True, server_default=sa.true()))

def downgrade():
    op.drop_column('site_settings', 'show_linkedin')
    op.drop_column('site_settings', 'show_youtube')
    op.drop_column('site_settings', 'show_whatsapp')
    op.drop_column('site_settings', 'show_telegram')
