"""Add SEO fields to products

Revision ID: 20251130_add_seo
Revises: 
Create Date: 2025-11-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251130_add_seo'
down_revision = None  # Update this to your latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Add SEO fields to products table
    op.add_column('products', sa.Column('seo_title', sa.String(length=60), nullable=True))
    op.add_column('products', sa.Column('seo_description', sa.String(length=160), nullable=True))
    op.add_column('products', sa.Column('seo_keywords', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('products', sa.Column('slug', sa.String(length=255), nullable=True))
    
    # Create indexes for better query performance
    op.create_index(op.f('ix_products_slug'), 'products', ['slug'], unique=True)
    op.create_index(op.f('ix_products_name'), 'products', ['name'], unique=False)
    op.create_index(op.f('ix_products_category_id'), 'products', ['category_id'], unique=False)
    op.create_index(op.f('ix_products_supplier_id'), 'products', ['supplier_id'], unique=False)
    op.create_index(op.f('ix_products_featured'), 'products', ['featured'], unique=False)
    op.create_index(op.f('ix_products_rating'), 'products', ['rating'], unique=False)
    op.create_index(op.f('ix_products_origin'), 'products', ['origin'], unique=False)
    op.create_index(op.f('ix_products_is_active'), 'products', ['is_active'], unique=False)


def downgrade():
    # Remove indexes
    op.drop_index(op.f('ix_products_is_active'), table_name='products')
    op.drop_index(op.f('ix_products_origin'), table_name='products')
    op.drop_index(op.f('ix_products_rating'), table_name='products')
    op.drop_index(op.f('ix_products_featured'), table_name='products')
    op.drop_index(op.f('ix_products_supplier_id'), table_name='products')
    op.drop_index(op.f('ix_products_category_id'), table_name='products')
    op.drop_index(op.f('ix_products_name'), table_name='products')
    op.drop_index(op.f('ix_products_slug'), table_name='products')
    
    # Remove SEO columns
    op.drop_column('products', 'slug')
    op.drop_column('products', 'seo_keywords')
    op.drop_column('products', 'seo_description')
    op.drop_column('products', 'seo_title')
