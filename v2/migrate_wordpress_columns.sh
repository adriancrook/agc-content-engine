#!/bin/bash
# Migration script for WordPress columns
# This adds the new WordPress columns to an existing database

echo "🔄 Checking for WordPress columns migration..."

# Run the migration script using Python
python3 migrate_add_wordpress_columns.py

if [ $? -eq 0 ]; then
    echo "✅ Migration completed successfully"
else
    echo "⚠️  Migration script failed or columns already exist"
fi
