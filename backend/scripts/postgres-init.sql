-- PostgreSQL Initialization Script for Banwee
-- This script sets up the database with optimizations and extensions

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE banwee_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'banwee_db')\gexec

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE banwee_db TO banwee;

-- Create schema for better organization
\c banwee_db;
CREATE SCHEMA IF NOT EXISTS banwee AUTHORIZATION banwee;
ALTER DATABASE banwee_db SET search_path TO banwee, public;

-- Set up monitoring views
CREATE OR REPLACE VIEW banwee.performance_stats AS
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation,
                most_common_vals::text,
                most_common_freqs::real[]
            FROM pg_stats 
            WHERE schemaname IN ('banwee', 'public');
-- Create function for cart cleanup (if needed)
CREATE OR REPLACE FUNCTION banwee.cleanup_expired_sessions()
RETURNS void AS $$
BEGIN
    -- This function can be used for any PostgreSQL-based session cleanup
    -- Currently, cart data is stored in Redis with TTL
    RAISE NOTICE 'Cart cleanup is handled by Redis TTL';
END;
$$ LANGUAGE plpgsql;

-- Create indexes for common queries (will be created by application)
-- These are placeholders - actual indexes will be created by the application

COMMENT ON SCHEMA banwee IS 'Main schema for Banwee application';
COMMENT ON FUNCTION banwee.cleanup_expired_sessions() IS 'Placeholder for session cleanup - Redis handles cart TTL';

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Banwee PostgreSQL initialization completed successfully';
    RAISE NOTICE 'Database: banwee_db';
    RAISE NOTICE 'Schema: banwee';
    RAISE NOTICE 'Extensions: uuid-ossp, pg_stat_statements, pg_trgm, btree_gin';
END $$;
