from connector import d1_executor

def conversation_storage_init_create_tables():
    """创建 Conversation 表."""
    sql = """
    CREATE TABLE IF NOT EXISTS Conversation (
        conversation_id TEXT PRIMARY KEY NOT NULL,
        project TEXT,
        brand TEXT,
        sequence TEXT NOT NULL DEFAULT 'sequential',
        status TEXT NOT NULL DEFAULT 'active',
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        latest_message_id TEXT,
        metadata TEXT
    );
    """
    d1_executor(sql)
    print("Conversation table created (or already exists).")

def create_message_table():
    """创建 Message 表。"""
    sql = """
    CREATE TABLE IF NOT EXISTS Message (
        message_id TEXT PRIMARY KEY NOT NULL,
        conversation_id TEXT NOT NULL,
        role TEXT NOT NULL,
        text TEXT NOT NULL,
        parent_message_id TEXT,
        timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        metadata TEXT,
        FOREIGN KEY (conversation_id) REFERENCES Conversation(conversation_id) ON DELETE CASCADE,
        FOREIGN KEY (parent_message_id) REFERENCES Message(message_id) ON DELETE CASCADE
    );
    """
    d1_executor(sql)
    print("Message table created (or already exists).")

def initialize_database():
    """初始化数据库，创建 Conversation 和 Message 表。"""
    conversation_storage_init_create_tables()
    create_message_table()
    print("Database initialization complete.")

if __name__ == "__main__":
    initialize_database()