from connector import cloudflare_d1_query
from typing import Any, Dict


def conversation_storage_init_create_tables(db_brand: str, db_metadata: Dict[str, Any]):
    """创建 Conversation 表."""
    if db_brand != "cloudflare_d1_lite":
        raise ValueError("Unsupported database brand")

    account_id = db_metadata.get("account_id")
    database_id = db_metadata.get("database_id")
    api_token = db_metadata.get("api_token")

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
    cloudflare_d1_query(
        account_id=account_id,
        database_id=database_id,
        api_token=api_token,
        sql_query=sql,
        params="[]",
    )
    print("Conversation table created (or already exists).")


def create_message_table(db_brand: str, db_metadata: Dict[str, Any]):
    """创建 Message 表。"""
    if db_brand != "cloudflare_d1_lite":
        raise ValueError("Unsupported database brand")

    account_id = db_metadata.get("account_id")
    database_id = db_metadata.get("database_id")
    api_token = db_metadata.get("api_token")

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
    cloudflare_d1_query(
        account_id=account_id,
        database_id=database_id,
        api_token=api_token,
        sql_query=sql,
        params="[]",
    )
    print("Message table created (or already exists).")


def initialize_database(db_brand: str, db_metadata: Dict[str, Any]):
    """初始化数据库，创建 Conversation 和 Message 表。"""
    conversation_storage_init_create_tables(db_brand, db_metadata)
    create_message_table(db_brand, db_metadata)
    print("Database initialization complete.")
