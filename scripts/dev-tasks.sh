#!/usr/bin/env bash

# SmartBase Development Automation Script

COMMAND=$1

case "$COMMAND" in
  up)
    echo "Starting SmartBase Development Environment..."
    # 1. Create the backend environment and install dependencies when missing
    set -e
    cd backend
    if [ ! -x "venv/bin/python" ]; then
        python3 -m venv venv
    fi
    if ! venv/bin/python -m pip --version >/dev/null 2>&1; then
        venv/bin/python -m ensurepip --upgrade
    fi
    if ! venv/bin/python -c "import flask, flask_cors, mysql.connector" >/dev/null 2>&1; then
        echo "Installing backend dependencies..."
        venv/bin/python -m pip install Flask flask-cors mysql-connector-python
    fi

    # 2. Install frontend dependencies before starting the backend
    cd ../frontend
    if [ ! -x "node_modules/.bin/vite" ]; then
        echo "Installing frontend dependencies..."
        npm install
    fi

    # 3. Run backend in background and start Vite
    cd ../backend
    venv/bin/python app/main.py &
    BACKEND_PID=$!
    trap 'kill "$BACKEND_PID" 2>/dev/null || true' EXIT

    cd ../frontend
    echo "Starting frontend dev server..."
    npm run dev -- --host
    
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