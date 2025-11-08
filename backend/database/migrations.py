"""
Simple Database Migration System for CLE
Handles basic database schema updates
"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from .connection import engine

SessionLocal = sessionmaker(bind=engine)

logger = logging.getLogger(__name__)

class Migration:
    """Represents a single database migration"""

    def __init__(self, version: str, description: str, upgrade_sql: str, downgrade_sql: str = ""):
        self.version = version
        self.description = description
        self.upgrade_sql = upgrade_sql
        self.downgrade_sql = downgrade_sql

class MigrationManager:
    """Manages database migrations"""

    def __init__(self):
        self.migrations: List[Migration] = []
        self._init_migration_table()
        self._register_migrations()

    def _init_migration_table(self):
        """Create the migration tracking table"""
        with SessionLocal() as session:
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(50) PRIMARY KEY,
                    description TEXT NOT NULL,
                    applied_at TIMESTAMP NOT NULL
                )
            """))
            session.commit()

    def _register_migrations(self):
        """Register available migrations"""

        # Migration 001: Initial schema
        self.migrations.append(Migration(
            version="001_initial_schema",
            description="Initial CLE database schema",
            upgrade_sql="""
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                CREATE INDEX IF NOT EXISTS idx_learning_cards_next_review ON learning_cards(next_review);
                CREATE INDEX IF NOT EXISTS idx_courses_title ON courses(title);
            """,
            downgrade_sql="""
                DROP INDEX IF EXISTS idx_users_email;
                DROP INDEX IF EXISTS idx_learning_cards_next_review;
                DROP INDEX IF EXISTS idx_courses_title;
            """
        ))

    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions"""
        with SessionLocal() as session:
            result = session.execute(text("SELECT version FROM schema_migrations ORDER BY version"))
            return [row[0] for row in result]

    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations"""
        applied = set(self.get_applied_migrations())
        return [m for m in self.migrations if m.version not in applied]

    def migrate_up(self) -> bool:
        """Apply pending migrations"""
        try:
            pending = self.get_pending_migrations()

            if not pending:
                logger.info("No pending migrations")
                return True

            logger.info(f"Applying {len(pending)} migrations")

            with SessionLocal() as session:
                for migration in pending:
                    statements = [stmt.strip() for stmt in migration.upgrade_sql.split(';') if stmt.strip()]
                    for statement in statements:
                        session.execute(text(statement))

                    session.execute(text("""
                        INSERT INTO schema_migrations (version, description, applied_at)
                        VALUES (:version, :description, datetime('now'))
                    """), {
                        'version': migration.version,
                        'description': migration.description
                    })

                session.commit()

            logger.info("Migrations applied successfully")
            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

    def get_migration_status(self) -> Dict[str, Any]:
        """Get migration status"""
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()

        return {
            "total_migrations": len(self.migrations),
            "applied_count": len(applied),
            "pending_count": len(pending),
            "applied_versions": applied,
            "pending_versions": [m.version for m in pending],
            "needs_migration": len(pending) > 0
        }

# Global migration manager
migration_manager = MigrationManager()

def migrate_database() -> bool:
    """Run database migrations"""
    try:
        return migration_manager.migrate_up()
    except Exception as e:
        logger.error(f"Database migration error: {e}")
        return False

def rollback_database() -> bool:
    """Rollback database (placeholder implementation)"""
    logger.info("Rollback not implemented in simple migration system")
    return True

def get_database_schema_info() -> Dict[str, Any]:
    """Get database schema information"""
    try:
        migration_status = migration_manager.get_migration_status()

        # Get table counts
        table_counts = {}
        with SessionLocal() as session:
            try:
                result = session.execute(text("""
                    SELECT name FROM sqlite_master WHERE type='table'
                """))
                tables = [row[0] for row in result]

                for table in tables:
                    try:
                        count_result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        table_counts[table] = count_result.scalar()
                    except Exception:
                        table_counts[table] = 0
            except Exception:
                pass

        return {
            "migration_status": migration_status,
            "table_counts": table_counts,
            "total_tables": len(table_counts)
        }

    except Exception as e:
        logger.error(f"Failed to get database schema info: {e}")
        return {
            "migration_status": {},
            "table_counts": {},
            "total_tables": 0
        }