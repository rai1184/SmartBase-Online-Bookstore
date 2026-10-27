#!/usr/bin/env bash

# SmartBase Development Automation Script

COMMAND=$1

case "$COMMAND" in
  up)
    echo "Starting SmartBase Development Environment..."
    # 1. Create the backend environment and install dependencies when missing
    set -e
    cd backend
    if [ ! -x "venv/bin/python" ] || ! venv/bin/python -c "import subprocess" >/dev/null 2>&1; then
        rm -rf venv
        python3 -m venv --without-pip venv
    fi
    if ! venv/bin/python -c "import flask, flask_cors, mysql.connector" >/dev/null 2>&1; then
        echo "Installing backend dependencies..."
        python3 -m pip --python venv/bin/python install Flask flask-cors mysql-connector-python
    fi

    # 2. Install frontend dependencies before starting the backend
    cd ../frontend
    if [ ! -x "node_modules/.bin/vite" ]; then
        echo "Installing frontend dependencies..."
        npm install
    fi

    # 3. Initialize the schema when the persistent database is empty
    cd ..
    DATABASE_TABLES=$(MYSQL_PWD="$MYSQL_PASSWORD" mysql \
        --host="$MYSQL_HOST" \
        --user="$MYSQL_USER" \
        --database="$MYSQL_DATABASE" \
        --batch \
        --skip-column-names \
        --execute="SHOW TABLES")
    if [ -z "$DATABASE_TABLES" ]; then
        echo "Initializing the empty database from init.sql..."
        MYSQL_PWD="$MYSQL_PASSWORD" mysql \
            --host="$MYSQL_HOST" \
            --user="$MYSQL_USER" \
            "$MYSQL_DATABASE" < init.sql
    elif ! printf '%s\n' "$DATABASE_TABLES" | grep -Fxq "Books"; then
        echo "Database has tables but is missing Books; refusing to import seed data automatically."
        echo "Inspect the database and apply the required schema changes manually."
        exit 1
    fi

    # 4. Run backend in background and start Vite
    cd backend
    venv/bin/python -m app.main &
    BACKEND_PID=$!
    FRONTEND_PID=
    cleanup() {
        for process_id in "$FRONTEND_PID" "$BACKEND_PID"; do
            if [ -n "$process_id" ] && kill -0 "$process_id" 2>/dev/null; then
                kill "$process_id" 2>/dev/null || true
            fi
        done
        wait "$FRONTEND_PID" 2>/dev/null || true
        wait "$BACKEND_PID" 2>/dev/null || true
    }
    trap cleanup EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM

    cd ../frontend
    echo "Starting frontend dev server..."
    npm run dev -- --host &
    FRONTEND_PID=$!
    wait -n "$BACKEND_PID" "$FRONTEND_PID"
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