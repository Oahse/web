-- Add profile fields to users table
-- SQLite doesn't support IF NOT EXISTS, so we'll just try to add them
-- If they already exist, the command will fail but that's okay

ALTER TABLE users ADD COLUMN age INTEGER;
ALTER TABLE users ADD COLUMN gender VARCHAR(50);
ALTER TABLE users ADD COLUMN country VARCHAR(100);
ALTER TABLE users ADD COLUMN language VARCHAR(10) DEFAULT 'en';
ALTER TABLE users ADD COLUMN timezone VARCHAR(100);
ALTER TABLE users ADD COLUMN verification_token VARCHAR(255);
ALTER TABLE users ADD COLUMN token_expiration TIMESTAMP;
