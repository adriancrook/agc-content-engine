"""
Migration: Add WordPress columns to articles_v2 table
Run this once to add the new columns for WordPress export functionality
"""

import sqlite3
import os

DB_PATH = "agc_v2.db"

def migrate():
    """Add WordPress columns to articles_v2 table"""

    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return False

    print(f"🔄 Migrating database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
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


if __name__ == "__main__":
    print("="*60)
    print("DATABASE MIGRATION: Add WordPress Columns")
    print("="*60)

    success = migrate()

    print("\n" + "="*60)
    if success:
        print("✅ MIGRATION SUCCESSFUL")
    else:
        print("❌ MIGRATION FAILED")
    print("="*60)
