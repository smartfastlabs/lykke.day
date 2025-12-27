#!/bin/bash
set -e

# Create the test database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE planned_test;
EOSQL

# Create the test user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE USER planned_test WITH PASSWORD 'password';
EOSQL

# Grant all privileges on the test database to the test user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    GRANT ALL PRIVILEGES ON DATABASE planned_test TO planned_test;
EOSQL

# Grant all privileges on the dev database to the main user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    GRANT ALL PRIVILEGES ON DATABASE planned_dev TO planned;
EOSQL

# Grant schema privileges on test database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "planned_test" <<-EOSQL
    GRANT ALL ON SCHEMA public TO planned_test;
EOSQL

# Grant schema privileges on dev database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "planned_dev" <<-EOSQL
    GRANT ALL ON SCHEMA public TO planned;
EOSQL
