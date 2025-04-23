CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    balance NUMERIC(12, 2) DEFAULT 0.00,
    added_balance NUMERIC(12, 2) DEFAULT 0.00,
    blocked_balance NUMERIC(12, 2) DEFAULT 0.00
);
