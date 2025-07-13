"""
Pytest configuration and fixtures for all tests.
"""

import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure ctutor_backend is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ctutor_backend.model import Base


@pytest.fixture(scope="session")
def database_url():
    """Get database URL from environment or use default test database."""
    env_vars = {
        'POSTGRES_HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'POSTGRES_PORT': os.environ.get('POSTGRES_PORT', '5432'),
        'POSTGRES_USER': os.environ.get('POSTGRES_USER', 'postgres'),
        'POSTGRES_PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgres_secret'),
        'POSTGRES_DB': os.environ.get('POSTGRES_DB', 'codeability')
    }
    
    return f"postgresql://{env_vars['POSTGRES_USER']}:{env_vars['POSTGRES_PASSWORD']}@{env_vars['POSTGRES_HOST']}:{env_vars['POSTGRES_PORT']}/{env_vars['POSTGRES_DB']}"


@pytest.fixture(scope="session")
def engine(database_url):
    """Create database engine."""
    return create_engine(database_url)


@pytest.fixture(scope="session")
def Session(engine):
    """Create session factory."""
    return sessionmaker(bind=engine)


@pytest.fixture
def session(Session):
    """Create a new database session for a test."""
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database(engine):
    """Set up test database with all extensions and initial schema."""
    # Note: In a real test environment, you would:
    # 1. Create a fresh test database
    # 2. Run all migrations
    # 3. Set up test data
    # For now, we assume the database exists
    pass