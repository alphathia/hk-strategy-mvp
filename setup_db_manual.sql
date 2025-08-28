-- Manual database setup commands
-- Run these one by one in PostgreSQL

-- Step 1: Connect as postgres user and create database
CREATE USER trader WITH PASSWORD 'YOUR_SECURE_PASSWORD';
CREATE DATABASE hk_strategy OWNER trader;
GRANT ALL PRIVILEGES ON DATABASE hk_strategy TO trader;

-- Step 2: Connect to hk_strategy database as trader user
-- Then run the init.sql file