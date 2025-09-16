# python
from collections.abc import Generator
from typing import Any, List

from utils.core import conversation_storage_put_message
from utils.core.conversation_storage_put_message import fetch_message_metadata
from dify_plugin import Tool

import json

def _normalize_tags(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        # supporte chaîne CSV: "tag1, tag2 ,tag3"
        items = [x.strip() for x in value.split(",") if x.strip() != ""]
    elif isinstance(value, (list, tuple, set)):
        items = [str(x).strip() for x in value]
    else:
        items = [str(value).strip()]
    # dédoublonnage insensible à la casse, on conserve la première casse rencontrée
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

class PutMessageTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator:
        db_brand = "cloudflare_d1_lite"

        account_id = self.runtime.credentials.get("cloudflare_account_id")
        database_id = self.runtime.credentials.get("cloudflare_d1_database_id")
        api_token = self.runtime.credentials.get("cloudflare_api_token")

        if not account_id or not database_id or not api_token:
            yield self.create_text_message(
                "Configuration manquante: veuillez renseigner cloudflare_account_id, "
                "cloudflare_d1_database_id et cloudflare_api_token dans les credentials du provider."
            )
            return

        db_metadata = {
            "account_id": account_id,
            "database_id": database_id,
            "api_token": api_token,
        }

        # inchangé: on conserve la sélection du rôle (assistant ou user) depuis l'UI
        conversation_id = tool_parameters.get("conversation_id","")
        role = tool_parameters["role"]
        text = tool_parameters["text"]
        parent_message_id = tool_parameters.get("parent_message_id", "")
        # message_id is optional; if omitted, we'll merge tags with latest message metadata of the conversation
        message_id = tool_parameters.get("message_id")

        # nouveau: tags optionnels sur le message
        tags = _normalize_tags(tool_parameters.get("tags", ""))
        # Merge with existing metadata (latest message of the conversation if message_id not provided)
        metadata = fetch_message_metadata(
            db_brand=db_brand,
            db_metadata=db_metadata,
            conversation_id=conversation_id or None,
            message_id=message_id or None,
        ) if conversation_id else {}

        if not isinstance(metadata, dict):
            metadata = {}

        existing_tags = _normalize_tags(metadata.get("tags"))
        # fusion unique add-if-not-exist
        merged = existing_tags + _normalize_tags(
            [t for t in tags if t.lower() not in {et.lower() for et in existing_tags}]
        )
        if merged:
            metadata["tags"] = ", ".join(merged)  # e.g. "tag1, tag2, tag3"

        result = conversation_storage_put_message(
            db_brand=db_brand,
            db_metadata=db_metadata,
            conversation_id=conversation_id,
            role=role,
            text=text,
            parent_message_id=parent_message_id,
            metadata=metadata if metadata else None,
        )
        # Return as JSON payload for the tool output
        yield self.create_json_message(result)
