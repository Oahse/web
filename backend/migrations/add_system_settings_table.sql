CREATE TABLE system_settings (
    id TEXT PRIMARY KEY NOT NULL,
    maintenance_mode BOOLEAN DEFAULT 0,
    registration_enabled BOOLEAN DEFAULT 1,
    max_file_size INTEGER DEFAULT 10,
    allowed_file_types TEXT DEFAULT 'jpg,jpeg,png,pdf',
    email_notifications BOOLEAN DEFAULT 1,
    sms_notifications BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);