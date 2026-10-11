#!/usr/bin/env bash

# SmartBase Development Automation Script

COMMAND=$1

case "$COMMAND" in
  up)
    echo "Starting SmartBase Development Environment..."
    # 1. Install or update backend dependencies
    cd backend
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -q Flask flask-cors mysql-connector-python
    
    # 2. Run backend in background
    python3 app.py &
    BACKEND_PID=$!
    
    # 3. Install or update frontend dependencies and start Vite with host flag
    cd ../frontend
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    echo "Starting frontend dev server..."
    npm run dev -- --host
    
    # Kill backend when frontend stops
    kill $BACKEND_PID
    ;;
    
  check)
    echo "Running code checks and tests..."
    cd backend && source venv/bin/activate && python3 -m unittest discover || true
    cd ../frontend && npm run lint || true
    echo "Checks complete!"
    ;;
    
  clean)
    echo "Cleaning up caches and temporary files..."
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type d -name "node_modules" -exec rm -rf {} +
    find . -type d -name "venv" -exec rm -rf {} +
    echo "Cleanup complete! Dependencies will be re-installed on next 'devup'."
    ;;
    
  *)
    echo "Usage: devup | devcheck | devclean"
    ;;
esac