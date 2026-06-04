#!/bin/bash
MYSQL_DATA="/home/runner/mysql-data"
MYSQL_RUN="/home/runner/mysql-run"
MYSQL_BIN=$(dirname $(which mysqld))

mkdir -p "$MYSQL_RUN"

# If data dir not initialized, initialize it
if [ ! -d "$MYSQL_DATA/mysql" ]; then
    echo "Initializing MySQL data directory..."
    mysqld --initialize-insecure --user=runner \
        --datadir="$MYSQL_DATA" 2>&1
fi

# Kill any previous mysqld
pkill -f mysqld 2>/dev/null; sleep 1

# Start MySQL
echo "Starting MySQL..."
mysqld --user=runner \
    --datadir="$MYSQL_DATA" \
    --socket="$MYSQL_RUN/mysql.sock" \
    --pid-file="$MYSQL_RUN/mysql.pid" \
    --port=3306 \
    --mysqlx=OFF \
    --log-error="$MYSQL_DATA/mysql.err" &

# Wait for MySQL to be ready
echo "Waiting for MySQL to start..."
for i in $(seq 1 30); do
    if mysqladmin ping --socket="$MYSQL_RUN/mysql.sock" -u root 2>/dev/null; then
        echo "MySQL is ready."
        break
    fi
    sleep 1
done

# Create database + user if needed
mysql -u root --socket="$MYSQL_RUN/mysql.sock" 2>/dev/null <<SQL
CREATE DATABASE IF NOT EXISTS autocare CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'autocare'@'localhost' IDENTIFIED BY 'autocare123';
GRANT ALL PRIVILEGES ON autocare.* TO 'autocare'@'localhost';
FLUSH PRIVILEGES;
SQL
echo "MySQL setup done."
