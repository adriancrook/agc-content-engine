#!/bin/bash
cd v2
export PYTHONPATH=/app/v2:$PYTHONPATH
exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}
