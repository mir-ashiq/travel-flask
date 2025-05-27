"""
Migration script to add show_facebook, show_instagram, and show_twitter columns to SiteSettings.

Revision ID: 20240527_add_show_social_to_sitesettings
Revises: d7ee0eedc236
Create Date: 2025-05-27
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240527_add_show_social_to_sitesettings'
down_revision = 'd7ee0eedc236'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('site_settings', sa.Column('show_facebook', sa.Boolean(), server_default=sa.true(), nullable=False))
    op.add_column('site_settings', sa.Column('show_instagram', sa.Boolean(), server_default=sa.true(), nullable=False))
    op.add_column('site_settings', sa.Column('show_twitter', sa.Boolean(), server_default=sa.true(), nullable=False))

def downgrade():
    op.drop_column('site_settings', 'show_facebook')
    op.drop_column('site_settings', 'show_instagram')
    op.drop_column('site_settings', 'show_twitter')
