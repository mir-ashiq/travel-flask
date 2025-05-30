"""
Migration script to add 'email' column to the testimonial table.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240527_add_email_to_testimonial'
down_revision = '20240526_add_published_to_tourpackage'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('testimonial', sa.Column('email', sa.String(length=120), nullable=True))

def downgrade():
    op.drop_column('testimonial', 'email')
