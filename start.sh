#!/bin/bash
set -e

echo "Starting Kisan2Consumer on Render..."
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
