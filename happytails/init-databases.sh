#!/bin/bash
set -e

# Create Keycloak database and user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE keycloak;
    CREATE USER keycloak WITH PASSWORD 'keycloak_password';
    GRANT ALL PRIVILEGES ON DATABASE keycloak TO keycloak;
EOSQL

# Grant schema permissions to keycloak user (required for PostgreSQL 15+)
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "keycloak" <<-EOSQL
    GRANT ALL ON SCHEMA public TO keycloak;
    ALTER DATABASE keycloak OWNER TO keycloak;
EOSQL

echo "Keycloak database and user created successfully!"
