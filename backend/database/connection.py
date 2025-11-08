"""
Database Connection and Configuration Management
Centralized database setup for CLE system
"""

import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cle_database.db")

# Create engine with appropriate configuration
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration
    engine = create_engine(
        DATABASE_URL,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
            "timeout": 20
        },
        echo=False  # Set to True for SQL logging
    )
else:
    # PostgreSQL/MySQL configuration
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=10,
        max_overflow=20,
        echo=False
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for all models
Base = declarative_base()

# Metadata for schema management
metadata = MetaData()

def get_db() -> Session:
    """
    Dependency function to get database session
    Usage: db = next(get_db())
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        return False

def drop_tables():
    """Drop all database tables (use with caution!)"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
        return True
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        return False

def reset_database():
    """Reset database by dropping and recreating all tables"""
    try:
        drop_tables()
        create_tables()
        logger.info("Database reset completed")
        return True
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        return False

def get_database_info():
    """Get information about the database connection"""
    return {
        "database_url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL,
        "driver": engine.dialect.name,
        "pool_size": getattr(engine.pool, 'size', 'N/A'),
        "max_overflow": getattr(engine.pool, 'max_overflow', 'N/A'),
        "echo": engine.echo
    }

# Database health check
def check_database_health():
    """Check if database connection is healthy"""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return {"status": "healthy", "message": "Database connection successful"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Database connection failed: {str(e)}"}

# Transaction management utilities
class DatabaseTransaction:
    """Context manager for database transactions"""

    def __init__(self, db: Session):
        self.db = db
        self.successful = False

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # No exception, commit the transaction
            try:
                self.db.commit()
                self.successful = True
            except Exception as e:
                self.db.rollback()
                logger.error(f"Failed to commit transaction: {e}")
                raise
        else:
            # Exception occurred, rollback the transaction
            try:
                self.db.rollback()
            except Exception as e:
                logger.error(f"Failed to rollback transaction: {e}")
                raise

def execute_transaction(db: Session, operation_func):
    """
    Execute a function within a database transaction
    Automatically commits on success, rolls back on failure
    """
    with DatabaseTransaction(db) as session:
        return operation_func(session)

# Database initialization for startup
def initialize_database():
    """
    Initialize the database with all required tables
    Should be called on application startup
    """
    try:
        # Create tables
        if not create_tables():
            raise Exception("Failed to create database tables")

        # Log database info
        info = get_database_info()
        logger.info(f"Database initialized: {info}")

        # Check health
        health = check_database_health()
        if health["status"] != "healthy":
            logger.warning(f"Database health check failed: {health['message']}")

        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False