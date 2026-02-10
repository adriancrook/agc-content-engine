"""
Migration: Add WordPress columns to articles_v2 table
Run this once to add the new columns for WordPress export functionality
Works with both SQLite (local) and PostgreSQL (Railway)
"""

import os
import sys

# Detect database type from DATABASE_URL env var
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///agc_v2.db")

def migrate():
    """Add WordPress columns to articles_v2 table"""

    if DATABASE_URL.startswith("sqlite"):
        return migrate_sqlite()
    elif DATABASE_URL.startswith("postgres"):
        return migrate_postgres()
    else:
        print(f"❌ Unknown database type: {DATABASE_URL}")
        return False


def migrate_sqlite():
    """Migrate SQLite database (local dev)"""
    import sqlite3

    db_path = DATABASE_URL.replace("sqlite:///", "")

    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False

    print(f"🔄 Migrating SQLite database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(articles_v2)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"\n📋 Existing columns: {len(existing_columns)}")

        # Define new WordPress columns
        new_columns = [
            ("wordpress_content", "TEXT"),
            ("wordpress_metadata", "JSON"),
            ("wordpress_export_ready", "BOOLEAN DEFAULT 0"),
            ("wordpress_validation_issues", "JSON"),
        ]

        # Add each column if it doesn't exist
        added = []
        skipped = []

        for col_name, col_type in new_columns:
            if col_name not in existing_columns:
                print(f"  ➕ Adding column: {col_name} ({col_type})")
                cursor.execute(f"ALTER TABLE articles_v2 ADD COLUMN {col_name} {col_type}")
                added.append(col_name)
            else:
                print(f"  ⏭️  Column exists: {col_name}")
                skipped.append(col_name)

        conn.commit()

        # Verify
        cursor.execute("PRAGMA table_info(articles_v2)")
        final_columns = [row[1] for row in cursor.fetchall()]

        print(f"\n✅ Migration complete!")
        print(f"   - Added: {len(added)} columns")
        print(f"   - Skipped: {len(skipped)} columns")
        print(f"   - Total columns now: {len(final_columns)}")

        if added:
            print(f"\n📝 New columns added:")
            for col in added:
                print(f"   - {col}")

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


def migrate_postgres():
    """Migrate PostgreSQL database (Railway)"""
    import psycopg2
    from urllib.parse import urlparse

    # Parse DATABASE_URL
    url = urlparse(DATABASE_URL.replace("postgres://", "postgresql://"))

    print(f"🔄 Migrating PostgreSQL database: {url.hostname}")

    try:
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port,
            user=url.username,
            password=url.password,
            database=url.path[1:]  # Remove leading slash
        )
        cursor = conn.cursor()

        # Check existing columns
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'articles_v2'
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"\n📋 Existing columns: {len(existing_columns)}")

        # Define new WordPress columns
        new_columns = [
            ("wordpress_content", "TEXT"),
            ("wordpress_metadata", "JSON"),
            ("wordpress_export_ready", "BOOLEAN DEFAULT FALSE"),
            ("wordpress_validation_issues", "JSON"),
        ]

        # Add each column if it doesn't exist
        added = []
        skipped = []

        for col_name, col_type in new_columns:
            if col_name not in existing_columns:
                print(f"  ➕ Adding column: {col_name} ({col_type})")
                cursor.execute(f"ALTER TABLE articles_v2 ADD COLUMN {col_name} {col_type}")
                added.append(col_name)
            else:
                print(f"  ⏭️  Column exists: {col_name}")
                skipped.append(col_name)

        conn.commit()

        # Verify
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'articles_v2'
        """)
        final_columns = [row[0] for row in cursor.fetchall()]

        print(f"\n✅ Migration complete!")
        print(f"   - Added: {len(added)} columns")
        print(f"   - Skipped: {len(skipped)} columns")
        print(f"   - Total columns now: {len(final_columns)}")

        if added:
            print(f"\n📝 New columns added:")
            for col in added:
                print(f"   - {col}")

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False

    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    print("="*60)
    print("DATABASE MIGRATION: Add WordPress Columns")
    print("="*60)
    print(f"Database: {DATABASE_URL[:50]}...")

    success = migrate()

    print("\n" + "="*60)
    if success:
        print("✅ MIGRATION SUCCESSFUL")
    else:
        print("❌ MIGRATION FAILED")
    print("="*60)
