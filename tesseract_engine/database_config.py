from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import os
from typing import Generator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    def __init__(self):
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///tesseract.db")
        self.POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
        self.MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        self.POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))
        
        # Create engine with connection pooling
        self.engine = create_engine(
            self.DATABASE_URL,
            poolclass=QueuePool,
            pool_size=self.POOL_SIZE,
            max_overflow=self.MAX_OVERFLOW,
            pool_timeout=self.POOL_TIMEOUT,
            pool_recycle=self.POOL_RECYCLE,
            pool_pre_ping=True  # Enable connection health checks
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    @contextmanager
    def get_db_session(self) -> Generator:
        """
        Context manager for database sessions with automatic cleanup
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()
    
    def init_db(self):
        """
        Initialize database and verify connection
        """
        try:
            # Test connection
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            return False
    
    def get_connection_info(self) -> dict:
        """
        Get database connection information
        """
        return {
            "url": self.DATABASE_URL,
            "pool_size": self.POOL_SIZE,
            "max_overflow": self.MAX_OVERFLOW,
            "pool_timeout": self.POOL_TIMEOUT,
            "pool_recycle": self.POOL_RECYCLE
        }

# Create global instance
db_config = DatabaseConfig() 