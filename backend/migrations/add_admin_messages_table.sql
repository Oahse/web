CREATE TABLE admin_messages (
    id TEXT PRIMARY KEY NOT NULL,
    sender_id TEXT REFERENCES users (id),
    sender_email VARCHAR(255),
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    read BOOLEAN DEFAULT 0,
    archived BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);