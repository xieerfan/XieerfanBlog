DROP TABLE IF EXISTS posts;
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL,      -- 'programming' 或 'thoughts'
    post_type TEXT,              -- 'experience' (经验) 或 'development' (开发)
    language TEXT,               -- 'Python', 'Rust', 'Vue' 等
    is_open_source BOOLEAN,      -- 0 为否, 1 为是
    project_name TEXT,           -- 项目名称
    content TEXT NOT NULL,       -- Markdown 原文
    thumb_url TEXT,              -- R2 头图链接
    date DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 初始化配置表（如果之前没建）
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT
-- );
INSERT OR IGNORE INTO config (key, value) VALUES ('nickname', '屑二凡');
INSERT OR IGNORE INTO config (key, value) VALUES ('bio', '写代码的mtf喵 | 无证含糖 | OIer');
INSERT OR IGNORE INTO config (key, value) VALUES ('avatar', 'avatar.jpg');