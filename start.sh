#!/bin/bash
set -e

cd "$(dirname "$0")"

MYSQL_DATA="/home/runner/mysql-data"
MYSQL_RUN="/home/runner/mysql-run"

mkdir -p "$MYSQL_RUN"

# Initialize MySQL data directory if needed
if [ ! -d "$MYSQL_DATA/mysql" ]; then
    echo "Initializing MySQL data directory..."
    mysqld --initialize-insecure --user=runner \
        --datadir="$MYSQL_DATA" 2>&1
fi

# Clean up stale socket if MySQL not responding
if [ -S "$MYSQL_RUN/mysql.sock" ]; then
    if ! mysqladmin ping --socket="$MYSQL_RUN/mysql.sock" -u root 2>/dev/null; then
        echo "Cleaning up stale MySQL socket..."
        rm -f "$MYSQL_RUN/mysql.sock" "$MYSQL_RUN/mysql.sock.lock" "$MYSQL_RUN/mysql.pid"
        pkill -f mysqld 2>/dev/null || true
        sleep 1
    fi
fi

# Start MySQL if not already running
if ! mysqladmin ping --socket="$MYSQL_RUN/mysql.sock" -u root 2>/dev/null; then
    echo "Starting MySQL..."
    mysqld --user=runner \
        --datadir="$MYSQL_DATA" \
        --socket="$MYSQL_RUN/mysql.sock" \
        --pid-file="$MYSQL_RUN/mysql.pid" \
        --port=3306 \
        --mysqlx=OFF \
        --log-error="$MYSQL_DATA/mysql.err" \
        --character-set-server=utf8mb4 \
        --collation-server=utf8mb4_unicode_ci &

    echo "Waiting for MySQL to be ready..."
    for i in $(seq 1 30); do
        if mysqladmin ping --socket="$MYSQL_RUN/mysql.sock" -u root 2>/dev/null; then
            echo "MySQL is ready."
            break
        fi
        sleep 1
    done
fi

# Create database and user
mysql -u root --socket="$MYSQL_RUN/mysql.sock" <<SQL
CREATE DATABASE IF NOT EXISTS autocare CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'autocare'@'localhost' IDENTIFIED BY 'autocare123';
GRANT ALL PRIVILEGES ON autocare.* TO 'autocare'@'localhost';
FLUSH PRIVILEGES;
SQL
echo "MySQL setup complete."

# Install Python deps
pip install -r requirements.txt -q

# Run Django migrations and setup
python manage.py migrate --noinput
python manage.py collectstatic --noinput 2>/dev/null || true
python manage.py seed 2>/dev/null || true

PORT="${PORT:-5000}"
echo "Starting Django on port $PORT..."
exec python manage.py runserver "0.0.0.0:$PORT"
