-- Create database if not exists
CREATE DATABASE IF NOT EXISTS work_records;
USE work_records;

-- Create pages table to store work record pages
CREATE TABLE pages (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    created_time DATETIME NOT NULL,
    last_edited_time DATETIME NOT NULL,
    database_id VARCHAR(36) NOT NULL
);

-- Create records table to store individual work records
CREATE TABLE records (
    id VARCHAR(36) PRIMARY KEY,
    page_id VARCHAR(36) NOT NULL,
    created_time DATETIME NOT NULL,
    last_edited_time DATETIME NOT NULL,
    title VARCHAR(255),
    type VARCHAR(50),
    note TEXT,
    timestamp DATETIME,
    status VARCHAR(50),
    details TEXT,
    request_from VARCHAR(255),
    FOREIGN KEY (page_id) REFERENCES pages(id)
);

-- Create co_workers table to store co-worker relationships
CREATE TABLE co_workers (
    record_id VARCHAR(36),
    co_worker_name VARCHAR(100),
    PRIMARY KEY (record_id, co_worker_name),
    FOREIGN KEY (record_id) REFERENCES records(id)
);

-- Create indexes for better query performance
CREATE INDEX idx_pages_title ON pages(title);
CREATE INDEX idx_records_timestamp ON records(timestamp);
CREATE INDEX idx_records_status ON records(status);
CREATE INDEX idx_records_created ON records(created_time);

-- Add charset and collation
ALTER DATABASE work_records CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
ALTER TABLE pages CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE records CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE co_workers CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; 