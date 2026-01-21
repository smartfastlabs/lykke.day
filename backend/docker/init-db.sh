#!/bin/bash
set -e

# Create the test database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE lykke_test;
EOSQL

# Create the test user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE USER lykke_test WITH PASSWORD 'password';
EOSQL

# Grant all privileges on the test database to the test user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    GRANT ALL PRIVILEGES ON DATABASE lykke_test TO lykke_test;
EOSQL

# Grant all privileges on the dev database to the main user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    GRANT ALL PRIVILEGES ON DATABASE lykke_dev TO lykke;
EOSQL

# Grant schema privileges on test database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "lykke_test" <<-EOSQL
    GRANT ALL ON SCHEMA public TO lykke_test;
EOSQL

# Grant schema privileges on dev database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "lykke_dev" <<-EOSQL
    GRANT ALL ON SCHEMA public TO lykke;
EOSQL
