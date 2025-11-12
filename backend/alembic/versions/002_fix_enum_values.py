"""Fix enum values to uppercase

Revision ID: 002
Revises: 001
Create Date: 2025-11-10 16:50:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop and recreate repeatinterval enum with uppercase values
    op.execute("ALTER TABLE events ALTER COLUMN repeat_interval DROP DEFAULT")
    op.execute("ALTER TABLE events ALTER COLUMN repeat_interval TYPE varchar USING repeat_interval::varchar")
    op.execute("DROP TYPE IF EXISTS repeatinterval CASCADE")
    op.execute("CREATE TYPE repeatinterval AS ENUM ('NONE', 'DAY', 'WEEK', 'MONTH', 'YEAR')")
    op.execute("ALTER TABLE events ALTER COLUMN repeat_interval TYPE repeatinterval USING repeat_interval::repeatinterval")
    op.execute("ALTER TABLE events ALTER COLUMN repeat_interval SET DEFAULT 'NONE'")
    
    # Drop and recreate attachmentkind enum with uppercase values  
    op.execute("ALTER TABLE attachments ALTER COLUMN kind TYPE varchar USING kind::varchar")
    op.execute("DROP TYPE IF EXISTS attachmentkind CASCADE")
    op.execute("CREATE TYPE attachmentkind AS ENUM ('IMAGE', 'VIDEO')")
    op.execute("ALTER TABLE attachments ALTER COLUMN kind TYPE attachmentkind USING kind::attachmentkind")


def downgrade() -> None:
    # Revert to lowercase
    op.execute("ALTER TABLE events ALTER COLUMN repeat_interval TYPE varchar USING repeat_interval::varchar")
    op.execute("DROP TYPE IF EXISTS repeatinterval")
    op.execute("CREATE TYPE repeatinterval AS ENUM ('none', 'day', 'week', 'month', 'year')")
    op.execute("ALTER TABLE events ALTER COLUMN repeat_interval TYPE repeatinterval USING repeat_interval::repeatinterval")
    
    op.execute("ALTER TABLE attachments ALTER COLUMN kind TYPE varchar USING kind::varchar")
    op.execute("DROP TYPE IF EXISTS attachmentkind")
    op.execute("CREATE TYPE attachmentkind AS ENUM ('image', 'video')")
    op.execute("ALTER TABLE attachments ALTER COLUMN kind TYPE attachmentkind USING kind::attachmentkind")
