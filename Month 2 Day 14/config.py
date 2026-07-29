# Database configuration for SQLAlchemy.
# Adjust db_url with your PostgreSQL credentials and database name.
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database connection URL: username, password, host, port, and database name.
db_url = 'postgresql://postgres:password@localhost:5432/telusko'
engine = create_engine(db_url)

# Create a configured SQLAlchemy session factory.
session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

