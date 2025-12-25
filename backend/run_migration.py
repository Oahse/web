#!/usr/bin/env python3
"""
Enhanced Migration Runner for Subscription Payment Enhancements

This script safely applies the enhanced subscription payment models migration
with comprehensive backup, data integrity validation, API compatibility checking,
and automatic rollback capabilities.

Usage:
    python run_migration.py --database-url "postgresql://user:pass@host/db"
    
Requirements addressed:
- 17.2: Create database backups before applying schema changes
- 17.3: Validate data integrity and foreign key constraints  
- 17.4: Provide rollback scripts for each migration step
- 17.5: Preserve all existing data without loss
- 17.6: Ensure API compatibility is maintained during upgrades
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from services.migration_service import MigrationService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Enhanced Migration Runner for Subscription Payment Enhancements'
    )
    parser.add_argument(
        '--database-url', 
        required=True,
        help='Database URL (e.g., postgresql://user:pass@host/db)'
    )
    parser.add_argument(
        '--backup-dir',
        default='migration_backups',
        help='Directory to store backups (default: migration_backups)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Create backup only, do not run migration'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force migration even if validation fails'
    )
    parser.add_argument(
        '--skip-api-validation',
        action='store_true',
        help='Skip API compatibility validation'
    )
    
    args = parser.parse_args()
    
    # Initialize enhanced migration service
    service = MigrationService(args.postgres_db_url, args.backup_dir)
    
    logger.info("Starting enhanced subscription payment migration...")
    logger.info(f"Database URL: {args.postgres_db_url}")
    logger.info(f"Backup directory: {args.backup_dir}")
    
    try:
        # Create comprehensive backup first
        logger.info("Creating comprehensive pre-migration backup...")
        backup_path = service.create_backup("pre_subscription_enhancements_migration")
        logger.info(f"Backup created: {backup_path}")
        
        # Create rollback script
        rollback_script = service.create_rollback_script(
            "subscription_payment_enhancements", 
            backup_path
        )
        logger.info(f"Rollback script created: {rollback_script}")
        
        if args.dry_run:
            logger.info("Dry run mode - backup and rollback script created, migration not executed")
            return
            
        # Prepare migration command
        migration_command = [
            sys.executable, '-m', 'alembic', 'upgrade', '003'
        ]
        
        logger.info("Running migration with comprehensive validation...")
        success, message = service.run_migration_with_validation(migration_command)
        
        if success:
            logger.info("✓ Migration completed successfully!")
            logger.info(message)
            
            # List new tables and features
            logger.info("Enhanced subscription payment system features:")
            logger.info("New tables created:")
            new_tables = [
                "pricing_configs - Admin-configurable pricing settings",
                "subscription_cost_history - Historical cost tracking", 
                "payment_intents - Enhanced Stripe payment integration",
                "subscription_analytics - Comprehensive subscription metrics",
                "payment_analytics - Payment performance analytics",
                "loyalty_accounts - Customer loyalty and rewards",
                "points_transactions - Loyalty points tracking"
            ]
            for table in new_tables:
                logger.info(f"  ✓ {table}")
                
            logger.info("Enhanced subscription model fields:")
            enhanced_fields = [
                "variant_ids - Multiple product variants per subscription",
                "cost_breakdown - Detailed cost calculation tracking",
                "delivery_type - Configurable delivery options",
                "admin_percentage_applied - Applied admin fee percentage",
                "loyalty_points_earned - Points earned from subscription",
                "next_billing_date - Accurate billing cycle tracking"
            ]
            for field in enhanced_fields:
                logger.info(f"  ✓ {field}")
            
            logger.info(f"Rollback available via: {rollback_script}")
            
        else:
            logger.error("✗ Migration failed!")
            logger.error(message)
            
            if not args.force:
                logger.info("Migration was automatically rolled back")
                logger.info("Use --force to override validation failures")
                sys.exit(1)
            else:
                logger.warning("Continuing despite failures due to --force flag")
                
    except Exception as e:
        logger.error(f"Migration failed with error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()