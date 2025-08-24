-- Users table - core user data
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    last_message_time INTEGER DEFAULT 0,
    coins REAL DEFAULT 0.0,
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- Shop items - available items for purchase
CREATE TABLE IF NOT EXISTS shop_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    category TEXT NOT NULL,
    effect_type TEXT,
    effect_value TEXT,
    is_consumable BOOLEAN DEFAULT 0,
    min_level INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT 1
);

-- User inventory - items owned by users
CREATE TABLE IF NOT EXISTS user_inventory (
    user_id TEXT,
    item_id INTEGER,
    quantity INTEGER DEFAULT 1,
    purchased_at INTEGER DEFAULT (strftime('%s', 'now')),
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    FOREIGN KEY (item_id) REFERENCES shop_items (item_id),
    PRIMARY KEY (user_id, item_id)
);

-- Active effects - temporary item effects
CREATE TABLE IF NOT EXISTS active_effects (
    user_id TEXT,
    effect_type TEXT,
    effect_value REAL,
    expires_at INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    PRIMARY KEY (user_id, effect_type)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_level ON users(level);
CREATE INDEX IF NOT EXISTS idx_users_xp ON users(xp);
CREATE INDEX IF NOT EXISTS idx_shop_category ON shop_items(category);
CREATE INDEX IF NOT EXISTS idx_active_effects_expires ON active_effects(expires_at);