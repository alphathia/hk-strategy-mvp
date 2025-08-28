-- Manual Database Setup Script
-- Run this as the postgres superuser

-- Create or update the trader user with the secure password
-- NOTE: This script requires DATABASE_PASSWORD environment variable to be set
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'trader') THEN
        ALTER USER trader WITH PASSWORD :'DATABASE_PASSWORD';
        RAISE NOTICE 'User trader password updated';
    ELSE
        CREATE USER trader WITH PASSWORD :'DATABASE_PASSWORD';
        RAISE NOTICE 'User trader created';
    END IF;
END
$$;

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE hk_strategy OWNER trader'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'hk_strategy')\gexec

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE hk_strategy TO trader;

-- Display confirmation
\echo 'Database setup complete!'
\echo 'User: trader'
\echo 'Database: hk_strategy'
\echo 'Password: [Set to secure value]'