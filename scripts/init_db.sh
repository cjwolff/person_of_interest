#!/bin/bash

# Create PostgreSQL user if it doesn't exist
sudo -u postgres psql -c "CREATE USER surveillance_user WITH PASSWORD '0ur0buroS8888';" || true

# Create databases
sudo -u postgres psql -c "CREATE DATABASE surveillance_db OWNER surveillance_user;" || true
sudo -u postgres psql -c "CREATE DATABASE test_db OWNER surveillance_user;" || true

# Grant privileges
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE surveillance_db TO surveillance_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE test_db TO surveillance_user;"

# Initialize Alembic
cd /opt/person_of_interest/server
alembic init alembic

# Run migrations
alembic upgrade head