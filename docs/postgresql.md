# PostgreSQL Setup

Local PostgreSQL database setup for the Lykke application running on Raspberry Pi.

## Installation

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

## Database Configuration

Create the user and database:

```bash
sudo -u postgres psql -c "CREATE USER lykke WITH PASSWORD 'password';"
sudo -u postgres psql -c "CREATE DATABASE lykke OWNER lykke;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE lykke TO lykke;"
```

## Verify Connection

```bash
psql -h localhost -U lykke -d lykke
```
