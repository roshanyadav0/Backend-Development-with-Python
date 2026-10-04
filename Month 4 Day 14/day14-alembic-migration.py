"""
Day 14 Alembic Migration: Add role field to members table

This migration adds:
1. role column with CHECK constraint
2. Default value: 'member'
3. Index on role column for faster queries
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import String, CheckConstraint, Index

# Identify this migration
revision = 'abc123def456'
down_revision = 'previous_migration_id'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add role column to members table.
    
    Changes:
    - Add role VARCHAR(20) column
    - Default to 'member'
    - Add CHECK constraint: role IN ('admin', 'member')
    - Add index for faster queries
    """
    
    # Create enum type first (if using PostgreSQL)
    # For MySQL, we'll use VARCHAR with CHECK
    
    # Step 1: Add role column (nullable initially)
    op.add_column(
        'members',
        sa.Column(
            'role',
            sa.String(20),
            server_default='member',  # Default for existing rows
            nullable=False
        )
    )
    
    # Step 2: Add CHECK constraint
    op.create_check_constraint(
        'check_valid_role',
        'members',
        "role IN ('admin', 'member')"
    )
    
    # Step 3: Create index on role for faster queries
    op.create_index(
        'idx_members_role',
        'members',
        ['role']
    )
    
    print("✓ Added role column to members table")
    print("✓ Default role: 'member'")
    print("✓ Valid values: 'admin', 'member'")


def downgrade():
    """
    Revert the role column addition.
    
    Removes:
    - role column
    - CHECK constraint
    - index
    """
    
    # Step 1: Drop index
    op.drop_index('idx_members_role', table_name='members')
    
    # Step 2: Drop CHECK constraint
    op.drop_constraint('check_valid_role', 'members')
    
    # Step 3: Drop column
    op.drop_column('members', 'role')
    
    print("✓ Removed role column from members table")


# ============================================================================
# Alternative: Using PostgreSQL-specific enum type
# ============================================================================

"""
If you're using PostgreSQL, use ENUM type for better type safety:

from alembic import op
import sqlalchemy as sa

revision = 'abc123def456'
down_revision = 'previous_migration_id'

def upgrade():
    # Create ENUM type
    op.execute("""
        CREATE TYPE role_enum AS ENUM ('admin', 'member')
    """)
    
    # Add column with ENUM type
    op.add_column(
        'members',
        sa.Column(
            'role',
            sa.Enum('admin', 'member', name='role_enum'),
            server_default='member',
            nullable=False
        )
    )
    
    # Create index
    op.create_index(
        'idx_members_role',
        'members',
        ['role']
    )

def downgrade():
    # Drop index
    op.drop_index('idx_members_role', table_name='members')
    
    # Drop column
    op.drop_column('members', 'role')
    
    # Drop ENUM type
    op.execute("DROP TYPE IF EXISTS role_enum CASCADE")
"""

# ============================================================================
# How to Run This Migration
# ============================================================================

"""
# Create migration file:
alembic revision --autogenerate -m "Add role field to members"

# Run upgrade:
alembic upgrade head

# Rollback:
alembic downgrade -1

# Check migration status:
alembic current
alembic history

# Show what will be migrated:
alembic upgrade head --sql
"""

# ============================================================================
# Migration with Data Update
# ============================================================================

"""
If you need to set roles based on existing data:

def upgrade():
    # 1. Add column with default
    op.add_column(
        'members',
        sa.Column('role', sa.String(20), server_default='member', nullable=False)
    )
    
    # 2. Update specific users to admin (e.g., first user)
    op.execute('''
        UPDATE members 
        SET role = 'admin' 
        WHERE email = 'admin@example.com'
    ''')
    
    # 3. Add constraints and index
    op.create_check_constraint(
        'check_valid_role',
        'members',
        "role IN ('admin', 'member')"
    )
    
    op.create_index('idx_members_role', 'members', ['role'])

def downgrade():
    op.drop_index('idx_members_role', table_name='members')
    op.drop_constraint('check_valid_role', 'members')
    op.drop_column('members', 'role')
"""

# ============================================================================
# Batch Migration (for SQLite which has limited ALTER TABLE)
# ============================================================================

"""
For SQLite, use batch operations:

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

def upgrade():
    with op.batch_alter_table('members', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('role', sa.String(20), server_default='member', nullable=False)
        )
        batch_op.create_index('idx_members_role', ['role'])

def downgrade():
    with op.batch_alter_table('members', schema=None) as batch_op:
        batch_op.drop_index('idx_members_role')
        batch_op.drop_column('role')
"""
