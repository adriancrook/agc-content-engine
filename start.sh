#!/bin/bash
cd v2

# Set Python path
export PYTHONPATH=/app/v2:$PYTHONPATH

# Run database migration (adds WordPress columns if needed)
echo "🔄 Running database migrations..."
python3 migrate_add_wordpress_columns.py || echo "⚠️  Migration skipped (columns may already exist)"

# Start server
echo "🚀 Starting server..."
exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}
