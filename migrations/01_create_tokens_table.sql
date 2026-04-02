-- Таблица для хранения токенов
CREATE TABLE IF NOT EXISTS tokens (
    id TEXT PRIMARY KEY,
    token_value TEXT NOT NULL UNIQUE,
    token_type TEXT NOT NULL CHECK(token_type IN ('access', 'refresh')),
    user_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    ip_address TEXT,
    is_blacklisted BOOLEAN DEFAULT 0,
    blacklisted_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Таблица для связи access и refresh токенов
CREATE TABLE IF NOT EXISTS token_pairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    access_token_id TEXT NOT NULL,
    refresh_token_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (access_token_id) REFERENCES tokens(id),
    FOREIGN KEY (refresh_token_id) REFERENCES tokens(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_tokens_user_id ON tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_tokens_expires_at ON tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_tokens_is_blacklisted ON tokens(is_blacklisted);
CREATE INDEX IF NOT EXISTS idx_token_pairs_user_id ON token_pairs(user_id);
