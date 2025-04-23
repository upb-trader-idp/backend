CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    symbol TEXT NOT NULL,
    quantity INT NOT NULL,
    price FLOAT NOT NULL,
    action TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    flag TEXT DEFAULT 'unprocessed',
);
