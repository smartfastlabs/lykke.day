# PostgreSQL Setup

Local PostgreSQL database setup for the Planned application running on Raspberry Pi.

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
sudo -u postgres psql -c "CREATE USER planned WITH PASSWORD 'password';"
sudo -u postgres psql -c "CREATE DATABASE planned OWNER planned;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE planned TO planned;"
```

## Verify Connection

```bash
psql -h localhost -U planned -d planned
```
