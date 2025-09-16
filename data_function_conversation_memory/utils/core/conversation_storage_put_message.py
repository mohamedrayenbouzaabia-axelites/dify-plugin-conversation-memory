# python
from typing import Optional, Dict, Any, List
import uuid
import json
from datetime import datetime
from utils.connector import cloudflare_d1_query


def fetch_message_metadata(
    db_brand: str,
    db_metadata: Dict[str, Any],
    conversation_id: Optional[str] = None,
    message_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetch metadata for a message. If message_id is provided, fetch that message's
    metadata; otherwise, fetch the latest message metadata of the conversation.
    """
    if db_brand != "cloudflare_d1_lite":
        raise ValueError("Unsupported database brand")

    account_id = db_metadata.get("account_id")
    database_id = db_metadata.get("database_id")
    api_token = db_metadata.get("api_token")

    if not message_id and not conversation_id:
        return {}

    if message_id:
        sql = "SELECT metadata FROM Message WHERE message_id = ? LIMIT 1;"
        params = json.dumps([message_id])
    else:
        sql = (
            "SELECT metadata FROM Message WHERE conversation_id = ? "
            "ORDER BY timestamp DESC LIMIT 1;"
        )
        params = json.dumps([conversation_id])

    res = cloudflare_d1_query(
        account_id=account_id,
        database_id=database_id,
        api_token=api_token,
        sql_query=sql,
        params=params,
    )

    if not res.get("success"):
        return {}

    rows = (
        res.get("metadata", {})
        .get("result", [{}])[0]
        .get("results", [])
    )
    if not rows:
        return {}

    raw = rows[0].get("metadata")
    if raw is None:
        return {}

    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return {}

def _normalize_tags(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items = [x.strip() for x in value.split(",") if x.strip() != ""]
    elif isinstance(value, (list, tuple, set)):
        items = [str(x).strip() for x in value]
    else:
        items = [str(value).strip()]
    seen = set()
    result = []
    for t in items:
        if not t:
            continue
        key = t.lower()
        if key not in seen:
            seen.add(key)
            result.append(t)
    return result

def conversation_storage_put_message(
    db_brand: str,
    db_metadata: Dict[str, Any],
    conversation_id: str,
    role: str,
    text: str,
    parent_message_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """
    Ajoute un nouveau message à une conversation (créée si nécessaire).
    Ajoute des tags optionnels uniques (add-if-not-exist) dans metadata.tags du Message.
    """
    if db_brand != "cloudflare_d1_lite":
        raise ValueError("Unsupported database brand")

    account_id = db_metadata.get("account_id")
    database_id = db_metadata.get("database_id")
    api_token = db_metadata.get("api_token")

    # 1) Ensure conversation exists
    select_conv_sql = (
        "SELECT conversation_id FROM Conversation WHERE conversation_id = ? LIMIT 1;"
    )
    select_conv_res = cloudflare_d1_query(
        account_id=account_id,
        database_id=database_id,
        api_token=api_token,
        sql_query=select_conv_sql,
        params=json.dumps([conversation_id]),
    )
    rows = (
        select_conv_res.get("metadata", {})
        .get("result", [{}])[0]
        .get("results", [])
        if select_conv_res.get("success")
        else []
    )
    if not rows:
        insert_conv_sql = (
            "INSERT INTO Conversation (conversation_id, status, metadata) "
            "VALUES (?, 'active', json('{}'));"
        )
        cloudflare_d1_query(
            account_id=account_id,
            database_id=database_id,
            api_token=api_token,
            sql_query=insert_conv_sql,
            params=json.dumps([conversation_id]),
        )

    # 2) Préparer metadata avec tags dédupliqués
    metadata = metadata or {}
    if not isinstance(metadata, dict):
        metadata = {}

    existing_tags = _normalize_tags(metadata.get("tags"))
    if existing_tags:
        # Store as a comma-separated string for consistency
        metadata["tags"] = ", ".join(existing_tags)
    else:
        metadata.pop("tags", None)

    message_id = str(uuid.uuid4())

    # 3) Insérer le message
    # Let the database set timestamp via DEFAULT CURRENT_TIMESTAMP
    insert_msg_sql = (
        "INSERT INTO Message (message_id, conversation_id, role, text, parent_message_id, metadata) "
        "VALUES (?, ?, ?, ?, ?, ?);"
    )
    cloudflare_d1_query(
        account_id=account_id,
        database_id=database_id,
        api_token=api_token,
        sql_query=insert_msg_sql,
        params=json.dumps(
            [
                message_id,
                conversation_id,
                role,
                json.dumps(text),
                parent_message_id,
                json.dumps(metadata, ensure_ascii=False),
            ]
        ),
    )

    return {"message_id": message_id, "conversation_id": conversation_id}
