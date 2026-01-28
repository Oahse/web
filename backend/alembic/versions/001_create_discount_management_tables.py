"""Create discount management tables

Revision ID: 001_discount_mgmt
Revises: 
Create Date: 2024-01-28 15:52:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_discount_mgmt'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create discounts table
    op.create_table('discounts',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(), nullable=True),
        sa.Column('updated_by', postgresql.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('minimum_amount', sa.Float(), nullable=True),
        sa.Column('maximum_discount', sa.Float(), nullable=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=False),
        sa.Column('usage_limit', sa.Integer(), nullable=True),
        sa.Column('used_count', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('idx_discounts_active', 'discounts', ['is_active'], unique=False)
    op.create_index('idx_discounts_active_valid', 'discounts', ['is_active', 'valid_from', 'valid_until'], unique=False)
    op.create_index('idx_discounts_code', 'discounts', ['code'], unique=False)
    op.create_index('idx_discounts_code_active', 'discounts', ['code', 'is_active'], unique=False)
    op.create_index('idx_discounts_type', 'discounts', ['type'], unique=False)
    op.create_index('idx_discounts_usage_limit', 'discounts', ['usage_limit'], unique=False)
    op.create_index('idx_discounts_used_count', 'discounts', ['used_count'], unique=False)
    op.create_index('idx_discounts_valid_from', 'discounts', ['valid_from'], unique=False)
    op.create_index('idx_discounts_valid_until', 'discounts', ['valid_until'], unique=False)

    # Create subscription_discounts table
    op.create_table('subscription_discounts',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(), nullable=True),
        sa.Column('updated_by', postgresql.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(), nullable=False),
        sa.Column('discount_id', postgresql.UUID(), nullable=False),
        sa.Column('discount_amount', sa.Float(), nullable=False),
        sa.Column('applied_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['discount_id'], ['discounts.id'], ),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_subscription_discounts_applied_at', 'subscription_discounts', ['applied_at'], unique=False)
    op.create_index('idx_subscription_discounts_discount_id', 'subscription_discounts', ['discount_id'], unique=False)
    op.create_index('idx_subscription_discounts_sub_discount', 'subscription_discounts', ['subscription_id', 'discount_id'], unique=False)
    op.create_index('idx_subscription_discounts_subscription_id', 'subscription_discounts', ['subscription_id'], unique=False)

    # Create product_removal_audit table
    op.create_table('product_removal_audit',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(), nullable=True),
        sa.Column('updated_by', postgresql.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(), nullable=False),
        sa.Column('product_id', postgresql.UUID(), nullable=False),
        sa.Column('removed_by', postgresql.UUID(), nullable=False),
        sa.Column('removed_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['removed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_product_removal_audit_product_id', 'product_removal_audit', ['product_id'], unique=False)
    op.create_index('idx_product_removal_audit_removed_at', 'product_removal_audit', ['removed_at'], unique=False)
    op.create_index('idx_product_removal_audit_removed_by', 'product_removal_audit', ['removed_by'], unique=False)
    op.create_index('idx_product_removal_audit_sub_product', 'product_removal_audit', ['subscription_id', 'product_id'], unique=False)
    op.create_index('idx_product_removal_audit_subscription_id', 'product_removal_audit', ['subscription_id'], unique=False)
    op.create_index('idx_product_removal_audit_user_date', 'product_removal_audit', ['removed_by', 'removed_at'], unique=False)

    # Create tax_rules table
    op.create_table('tax_rules',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(), nullable=True),
        sa.Column('updated_by', postgresql.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('location_code', sa.String(length=10), nullable=False),
        sa.Column('tax_rate', sa.Float(), nullable=False),
        sa.Column('minimum_tax', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_tax_rules_active', 'tax_rules', ['is_active'], unique=False)
    op.create_index('idx_tax_rules_location_active', 'tax_rules', ['location_code', 'is_active'], unique=False)
    op.create_index('idx_tax_rules_location_code', 'tax_rules', ['location_code'], unique=False)
    op.create_index('idx_tax_rules_tax_rate', 'tax_rules', ['tax_rate'], unique=False)

    # Create shipping_rules table
    op.create_table('shipping_rules',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(), nullable=True),
        sa.Column('updated_by', postgresql.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('location_code', sa.String(length=10), nullable=False),
        sa.Column('weight_min', sa.Float(), nullable=False),
        sa.Column('weight_max', sa.Float(), nullable=False),
        sa.Column('base_rate', sa.Float(), nullable=False),
        sa.Column('minimum_shipping', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_shipping_rules_active', 'shipping_rules', ['is_active'], unique=False)
    op.create_index('idx_shipping_rules_base_rate', 'shipping_rules', ['base_rate'], unique=False)
    op.create_index('idx_shipping_rules_location_active', 'shipping_rules', ['location_code', 'is_active'], unique=False)
    op.create_index('idx_shipping_rules_location_code', 'shipping_rules', ['location_code'], unique=False)
    op.create_index('idx_shipping_rules_weight_active', 'shipping_rules', ['weight_min', 'weight_max', 'is_active'], unique=False)
    op.create_index('idx_shipping_rules_weight_range', 'shipping_rules', ['weight_min', 'weight_max'], unique=False)

    # Create subscription_products table
    op.create_table('subscription_products',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(), nullable=True),
        sa.Column('updated_by', postgresql.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(), nullable=False),
        sa.Column('product_id', postgresql.UUID(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('total_price', sa.Float(), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('removed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('removed_by', postgresql.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['removed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_subscription_products_active', 'subscription_products', ['subscription_id', 'removed_at'], unique=False)
    op.create_index('idx_subscription_products_product_id', 'subscription_products', ['product_id'], unique=False)
    op.create_index('idx_subscription_products_removed_at', 'subscription_products', ['removed_at'], unique=False)
    op.create_index('idx_subscription_products_removed_by', 'subscription_products', ['removed_by'], unique=False)
    op.create_index('idx_subscription_products_sub_product', 'subscription_products', ['subscription_id', 'product_id'], unique=False)
    op.create_index('idx_subscription_products_subscription_id', 'subscription_products', ['subscription_id'], unique=False)

    # Add pricing structure columns to subscriptions table
    op.add_column('subscriptions', sa.Column('subtotal', sa.Float(), nullable=True, default=0.0))
    op.add_column('subscriptions', sa.Column('discount_amount', sa.Float(), nullable=True, default=0.0))
    op.add_column('subscriptions', sa.Column('total', sa.Float(), nullable=True, default=0.0))
    op.add_column('subscriptions', sa.Column('tax_validated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('subscriptions', sa.Column('shipping_validated_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove columns from subscriptions table
    op.drop_column('subscriptions', 'shipping_validated_at')
    op.drop_column('subscriptions', 'tax_validated_at')
    op.drop_column('subscriptions', 'total')
    op.drop_column('subscriptions', 'discount_amount')
    op.drop_column('subscriptions', 'subtotal')

    # Drop tables in reverse order
    op.drop_table('subscription_products')
    op.drop_table('shipping_rules')
    op.drop_table('tax_rules')
    op.drop_table('product_removal_audit')
    op.drop_table('subscription_discounts')
    op.drop_table('discounts')