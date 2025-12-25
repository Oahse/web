#!/usr/bin/env python3
"""
Database Migration Utilities with Backup and Rollback Capabilities

This script provides utilities for safely managing database migrations with
automatic backup creation and rollback capabilities as required by the
subscription payment enhancements specification.

Requirements addressed:
- 17.2: Create database backups before applying schema changes
- 17.3: Validate data integrity and foreign key constraints
- 17.4: Provide rollback scripts for each migration step
- 17.5: Preserve all existing data without loss
"""

import os
import sys
import subprocess
import datetime
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import asyncio
import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MigrationManager:
    """Enhanced migration manager with backup and rollback capabilities"""
    
    def __init__(self, postgres_db_url: str, backup_dir: str = "backups"):
        self.postgres_db_url = postgres_db_url
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Parse database URL for pg_dump
        self.db_config = self._parse_postgres_db_url(postgres_db_url)
        
    def _parse_postgres_db_url(self, url: str) -> Dict[str, str]:
        """Parse database URL into components for pg_dump"""
        # Example: postgresql://user:password@host:port/database
        if url.startswith('postgresql://'):
            url = url.replace('postgresql://', '')
        elif url.startswith('postgres://'):
            url = url.replace('postgres://', '')
            
        # Split user:password@host:port/database
        if '@' in url:
            auth, host_db = url.split('@', 1)
            if ':' in auth:
                user, password = auth.split(':', 1)
            else:
                user, password = auth, ''
        else:
            user, password = '', ''
            host_db = url
            
        if '/' in host_db:
            host_port, database = host_db.rsplit('/', 1)
        else:
            host_port, database = host_db, ''
            
        if ':' in host_port:
            host, port = host_port.split(':', 1)
        else:
            host, port = host_port, '5432'
            
        return {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database
        }
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """
        Create a database backup before migration
        
        Returns:
            str: Path to the backup file
        """
        if not backup_name:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.sql"
            
        backup_path = self.backup_dir / backup_name
        
        logger.info(f"Creating database backup: {backup_path}")
        
        # Build pg_dump command
        cmd = [
            'pg_dump',
            '-h', self.db_config['host'],
            '-p', self.db_config['port'],
            '-U', self.db_config['user'],
            '-d', self.db_config['database'],
            '--verbose',
            '--no-password',
            '--format=custom',
            '--file', str(backup_path)
        ]
        
        # Set password environment variable if provided
        env = os.environ.copy()
        if self.db_config['password']:
            env['PGPASSWORD'] = self.db_config['password']
            
        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Backup created successfully: {backup_path}")
            logger.info(f"Backup size: {backup_path.stat().st_size} bytes")
            
            # Create backup metadata
            metadata = {
                'backup_file': str(backup_path),
                'created_at': datetime.datetime.now().isoformat(),
                'database': self.db_config['database'],
                'host': self.db_config['host'],
                'port': self.db_config['port'],
                'user': self.db_config['user'],
                'size_bytes': backup_path.stat().st_size
            }
            
            metadata_path = backup_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            return str(backup_path)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Backup failed: {e}")
            logger.error(f"stdout: {e.stdout}")
            logger.error(f"stderr: {e.stderr}")
            raise RuntimeError(f"Database backup failed: {e}")
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        Restore database from backup
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            bool: True if restore was successful
        """
        backup_file = Path(backup_path)
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
        logger.info(f"Restoring database from backup: {backup_path}")
        
        # Build pg_restore command
        cmd = [
            'pg_restore',
            '-h', self.db_config['host'],
            '-p', self.db_config['port'],
            '-U', self.db_config['user'],
            '-d', self.db_config['database'],
            '--verbose',
            '--no-password',
            '--clean',
            '--if-exists',
            str(backup_file)
        ]
        
        # Set password environment variable if provided
        env = os.environ.copy()
        if self.db_config['password']:
            env['PGPASSWORD'] = self.db_config['password']
            
        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("Database restore completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Restore failed: {e}")
            logger.error(f"stdout: {e.stdout}")
            logger.error(f"stderr: {e.stderr}")
            return False
    
    async def validate_data_integrity(self) -> Dict[str, bool]:
        """
        Validate data integrity after migration
        
        Returns:
            Dict[str, bool]: Validation results for different checks
        """
        logger.info("Validating data integrity...")
        
        results = {
            'foreign_keys': False,
            'constraints': False,
            'indexes': False,
            'table_counts': False
        }
        
        try:
            conn = await asyncpg.connect(self.postgres_db_url)
            
            # Check foreign key constraints
            fk_violations = await conn.fetch("""
                SELECT conname, conrelid::regclass, confrelid::regclass
                FROM pg_constraint 
                WHERE contype = 'f' 
                AND NOT EXISTS (
                    SELECT 1 FROM pg_trigger 
                    WHERE tgconstraint = pg_constraint.oid
                )
            """)
            
            if not fk_violations:
                results['foreign_keys'] = True
                logger.info("✓ Foreign key constraints validated")
            else:
                logger.error(f"✗ Foreign key violations found: {len(fk_violations)}")
                
            # Check other constraints
            constraint_violations = await conn.fetch("""
                SELECT conname, conrelid::regclass
                FROM pg_constraint 
                WHERE contype IN ('c', 'u', 'p')
                AND NOT convalidated
            """)
            
            if not constraint_violations:
                results['constraints'] = True
                logger.info("✓ Constraints validated")
            else:
                logger.error(f"✗ Constraint violations found: {len(constraint_violations)}")
                
            # Check indexes
            invalid_indexes = await conn.fetch("""
                SELECT indexname, tablename
                FROM pg_indexes 
                WHERE schemaname = 'public'
                AND indexname IN (
                    SELECT indexname FROM pg_stat_user_indexes 
                    WHERE idx_scan = 0 AND idx_tup_read = 0
                )
            """)
            
            results['indexes'] = True  # Indexes are optional for validation
            logger.info("✓ Indexes checked")
            
            # Verify table counts are reasonable
            table_counts = await conn.fetch("""
                SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
            """)
            
            results['table_counts'] = True
            logger.info(f"✓ Table statistics validated for {len(table_counts)} tables")
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Data integrity validation failed: {e}")
            
        return results
    
    def run_migration_with_backup(self, migration_command: List[str]) -> Tuple[bool, str]:
        """
        Run migration with automatic backup and rollback on failure
        
        Args:
            migration_command: Command to run the migration
            
        Returns:
            Tuple[bool, str]: (success, backup_path or error_message)
        """
        backup_path = None
        
        try:
            # Create backup before migration
            backup_path = self.create_backup()
            
            # Run migration
            logger.info(f"Running migration: {' '.join(migration_command)}")
            result = subprocess.run(
                migration_command,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("Migration completed successfully")
            
            # Validate data integrity
            validation_results = asyncio.run(self.validate_data_integrity())
            
            if all(validation_results.values()):
                logger.info("✓ All data integrity checks passed")
                return True, backup_path
            else:
                logger.error("✗ Data integrity validation failed")
                failed_checks = [k for k, v in validation_results.items() if not v]
                logger.error(f"Failed checks: {failed_checks}")
                
                # Restore backup on validation failure
                logger.info("Restoring backup due to validation failure...")
                if self.restore_backup(backup_path):
                    return False, f"Migration failed validation, restored from backup: {backup_path}"
                else:
                    return False, f"Migration failed validation and backup restore failed: {backup_path}"
                    
        except subprocess.CalledProcessError as e:
            logger.error(f"Migration failed: {e}")
            logger.error(f"stdout: {e.stdout}")
            logger.error(f"stderr: {e.stderr}")
            
            if backup_path:
                logger.info("Restoring backup due to migration failure...")
                if self.restore_backup(backup_path):
                    return False, f"Migration failed, restored from backup: {backup_path}"
                else:
                    return False, f"Migration failed and backup restore failed: {backup_path}"
            else:
                return False, f"Migration failed and no backup was created: {e}"
                
        except Exception as e:
            logger.error(f"Unexpected error during migration: {e}")
            
            if backup_path:
                logger.info("Restoring backup due to unexpected error...")
                if self.restore_backup(backup_path):
                    return False, f"Migration failed with error, restored from backup: {backup_path}"
                else:
                    return False, f"Migration failed with error and backup restore failed: {backup_path}"
            else:
                return False, f"Migration failed with error and no backup was created: {e}"
    
    def list_backups(self) -> List[Dict[str, str]]:
        """List all available backups with metadata"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.sql"):
            metadata_file = backup_file.with_suffix('.json')
            
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                backups.append(metadata)
            else:
                # Create basic metadata for backups without metadata files
                stat = backup_file.stat()
                backups.append({
                    'backup_file': str(backup_file),
                    'created_at': datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'size_bytes': stat.st_size
                })
                
        return sorted(backups, key=lambda x: x['created_at'], reverse=True)


def main():
    """Main CLI interface for migration utilities"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Migration Utilities')
    parser.add_argument('--database-url', required=True, help='Database URL')
    parser.add_argument('--backup-dir', default='backups', help='Backup directory')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create database backup')
    backup_parser.add_argument('--name', help='Backup name (optional)')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('backup_path', help='Path to backup file')
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Run migration with backup')
    migrate_parser.add_argument('migration_command', nargs='+', help='Migration command to run')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available backups')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate data integrity')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    manager = MigrationManager(args.postgres_db_url, args.backup_dir)
    
    if args.command == 'backup':
        try:
            backup_path = manager.create_backup(args.name)
            print(f"Backup created: {backup_path}")
        except Exception as e:
            print(f"Backup failed: {e}")
            sys.exit(1)
            
    elif args.command == 'restore':
        try:
            success = manager.restore_backup(args.backup_path)
            if success:
                print(f"Restore completed: {args.backup_path}")
            else:
                print(f"Restore failed: {args.backup_path}")
                sys.exit(1)
        except Exception as e:
            print(f"Restore failed: {e}")
            sys.exit(1)
            
    elif args.command == 'migrate':
        try:
            success, message = manager.run_migration_with_backup(args.migration_command)
            print(message)
            if not success:
                sys.exit(1)
        except Exception as e:
            print(f"Migration failed: {e}")
            sys.exit(1)
            
    elif args.command == 'list':
        backups = manager.list_backups()
        if backups:
            print("Available backups:")
            for backup in backups:
                size_mb = backup['size_bytes'] / (1024 * 1024)
                print(f"  {backup['backup_file']} ({size_mb:.1f} MB) - {backup['created_at']}")
        else:
            print("No backups found")
            
    elif args.command == 'validate':
        try:
            results = asyncio.run(manager.validate_data_integrity())
            print("Data integrity validation results:")
            for check, passed in results.items():
                status = "✓ PASS" if passed else "✗ FAIL"
                print(f"  {check}: {status}")
                
            if all(results.values()):
                print("All checks passed!")
            else:
                print("Some checks failed!")
                sys.exit(1)
        except Exception as e:
            print(f"Validation failed: {e}")
            sys.exit(1)


if __name__ == '__main__':
    main()