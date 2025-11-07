#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# --- 1. Environment variables check ---
# This function ensures all necessary database environment variables are set.
check_env_vars() {
    echo "Checking for necessary environment variables..."
    if [ -z "${DB_HOST}" ]; then echo "Error: DB_HOST not set." >&2; exit 1; fi
    if [ -z "${DB_PORT}" ]; then echo "Error: DB_PORT not set." >&2; exit 1; fi
    if [ -z "${DB_USER}" ]; then echo "Error: DB_USER not set." >&2; exit 1; fi
    if [ -z "${DB_NAME}" ]; then echo "Error: DB_NAME not set." >&2; exit 1; fi
    if [ -z "${DB_PASSWORD}" ]; then echo "Error: DB_PASSWORD not set." >&2; exit 1; fi
    if [ -z "${REDIS_URL}" ]; then echo "Error: REDIS_URL not set." >&2; exit 1; fi
    echo "Environment variables are set."
}

# --- 2. Wait for the database to be ready ---
# This function uses pg_isready to poll the database until it's ready to accept connections.
# NOTE: This requires the 'postgresql-client' package to be installed in the Docker image.
wait_for_db() {
    echo "Waiting for PostgreSQL to be ready..."
    until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"; do
        echo "PostgreSQL is not yet ready. Sleeping for 5 seconds..."
        sleep 5
    done
    echo "PostgreSQL is ready."
}

wait_for_redis() {
    echo "Waiting for Redis to be ready..."
    
    # Use the -u flag to pass the full URL.
    # redis-cli (v6+) handles all parsing, auth, and TLS (for rediss://) automatically.
    # We add '|| true' so the 'until' loop doesn't exit on a connection error.
    until (redis-cli -u "$REDIS_URL" ping 2>/dev/null | grep -q 'PONG') || true; do
        echo "Redis is not yet ready. Sleeping for 5 seconds..."
        sleep 5
    done
    
    echo "Redis is ready."
}

# --- 3. Function to handle database initialization and migration ---
initialize_db() {
    export FLASK_ENV="development"
        # Determine the migrations directory based on the environment
    if [ "$FLASK_ENV" = "development" ]; then
        migrations_dir="./migrations"
        echo "Running in 'development' mode. Using migrations path: $migrations_dir"
    else
        # Default behavior for production or any other environment
        migrations_dir="/app/migrations"
        echo "Running in '$FLASK_ENV' mode. Using migrations path: $migrations_dir"
    fi

    # Check if the migrations directory exists
    if [ ! -d "$migrations_dir" ]; then
        echo "Migrations directory '$migrations_dir' not found. Skipping migrations."
        return 0 # Exit gracefully if there are no migrations to run
    fi

    # Set the PGPASSWORD environment variable for psql, then ensure it's unset on exit.
    export PGPASSWORD="$DB_PASSWORD"
    trap 'unset PGPASSWORD; echo "PGPASSWORD unset."' EXIT

    # Apply any pending database migrations.
    echo "Applying database migrations..."
    flask db upgrade

    # Check the exit status of the migration command.
    local exit_status=$?
    if [ $exit_status -ne 0 ]; then
        echo "Error: 'flask db upgrade' failed with status $exit_status." >&2
        return 1
    fi
    echo "Database migrations applied successfully."
}

# --- Main Execution ---

check_env_vars
wait_for_db
wait_for_redis

# Run database initialization and exit if it fails.
initialize_db || exit 1

# Start the Gunicorn server in the background.
echo "Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:5000 --timeout 60 -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 4 run:app

# Wait for any background processes to finish.
# This keeps the container running.
wait
