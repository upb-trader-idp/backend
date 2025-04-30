CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    balance NUMERIC(12, 2) DEFAULT 0.00,
    added_balance NUMERIC(12, 2) DEFAULT 0.00
);

CREATE TABLE IF NOT EXISTS portfolio (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    quantity INT NOT NULL CHECK (quantity >= 0),
    price NUMERIC(12, 2) NOT NULL CHECK (price >= 0)
);

CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    symbol TEXT NOT NULL,
    quantity INT NOT NULL,
    price FLOAT NOT NULL,
    action TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    flag TEXT DEFAULT 'unprocessed'
);
