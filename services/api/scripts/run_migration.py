"""
Run database migrations for RAAS API.
Usage: poetry run python scripts/run_migration.py <migration_file>
"""
import sys
import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


async def run_migration(migration_file: str, database_url: str):
    """Execute SQL migration file"""
    engine = create_async_engine(database_url)

    # Read migration SQL
    migration_path = Path(__file__).parent.parent / "app" / "migrations" / migration_file

    if not migration_path.exists():
        print(f"ERROR: Migration file not found: {migration_path}")
        sys.exit(1)

    with open(migration_path, "r") as f:
        sql = f.read()

    # Execute migration
    async with engine.begin() as conn:
        # Split by semicolon for multiple statements
        statements = [s.strip() for s in sql.split(";") if s.strip()]

        for statement in statements:
            print(f"Executing: {statement[:100]}...")
            await conn.execute(text(statement))

    print(f"✓ Migration {migration_file} completed successfully")
    await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: poetry run python scripts/run_migration.py <migration_file>")
        print("Example: poetry run python scripts/run_migration.py add_fts_index.sql")
        sys.exit(1)

    migration_file = sys.argv[1]

    # Get DATABASE_URL from environment
    import os
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    asyncio.run(run_migration(migration_file, database_url))
