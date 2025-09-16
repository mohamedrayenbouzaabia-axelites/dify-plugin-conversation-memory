# python
# conversation_storage_put_tag.py
from typing import Any, Dict, List
import json
from utils.connector import cloudflare_d1_query

def fetch_conversation_metadata(db_brand: str, db_metadata: Dict[str, Any], conversation_id: str) -> Dict[str, Any]:
    # Fetch conversation metadata using proper connector signature
    if db_brand != "cloudflare_d1_lite":
        raise ValueError("Unsupported database brand")
    if not conversation_id:
        return {}

    account_id = db_metadata.get("account_id")
    database_id = db_metadata.get("database_id")
    api_token = db_metadata.get("api_token")

    select_sql = "SELECT metadata FROM Conversation WHERE conversation_id = ? LIMIT 1;"
    select_res = cloudflare_d1_query(
        account_id=account_id,
        database_id=database_id,
        api_token=api_token,
        sql_query=select_sql,
        params=json.dumps([conversation_id]),
    )
    if not select_res.get("success"):
        return {}

    rows = (
        select_res.get("metadata", {})
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
    if isinstance(raw, str) and raw.strip():
        try:
            return json.loads(raw)
        except Exception:
            return {}
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
    out = []
    for t in items:
        if not t:
            continue
        k = t.lower()
        if k not in seen:
            seen.add(k)
            out.append(t)
    return out

def conversation_storage_put_tag(
    db_brand: str,
    db_metadata: Dict[str, Any],
    conversation_id: str,
    tags: List[str],
) -> Dict[str, Any]:
    # Normalisation des tags entrants
    tags = _normalize_tags(tags)
    if not tags:
        return {"ok": True, "message": "no-op", "tags": []}

    # Récupération du metadata de la conversation (sans requête si ID vide)
    existing_meta = fetch_conversation_metadata(db_brand, db_metadata, conversation_id)
    print("existing_meta:", existing_meta)
    if not isinstance(existing_meta, dict):
        existing_meta = {}

    # Fusion/déduplication insensible à la casse
    existing_tags = _normalize_tags(existing_meta.get("tags"))
    existing_map = {t.lower(): t for t in existing_tags}
    for t in tags:
        if t.lower() not in existing_map:
            existing_map[t.lower()] = t
    merged_tags = list(existing_map.values())

    # Conserver le format CSV si c’est la convention
    existing_meta["tags"] = ", ".join(merged_tags)

    # Mise à jour (no updated_at column in schema)
    update_sql = "UPDATE Conversation SET metadata = ? WHERE conversation_id = ?;"
    account_id = db_metadata.get("account_id")
    database_id = db_metadata.get("database_id")
    api_token = db_metadata.get("api_token")
    cloudflare_d1_query(
        account_id=account_id,
        database_id=database_id,
        api_token=api_token,
        sql_query=update_sql,
        params=json.dumps([json.dumps(existing_meta, ensure_ascii=False), conversation_id]),
    )

    return {"ok": True, "tags": merged_tags}
