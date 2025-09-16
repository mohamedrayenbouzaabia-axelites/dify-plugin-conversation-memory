# python
from collections.abc import Generator
from typing import Any, List

from utils.core import conversation_storage_put_message

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

import json

def _normalize_tags(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        # supporte chaîne CSV: "tag1, tag2 ,tag3"
        items = [x.strip() for x in value.split(",")]
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
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        db_brand = "cloudflare_d1_lite"
        db_metadata = {
            "account_id": tool_parameters["cloudflare_account_id"],
            "database_id": tool_parameters["cloudflare_d1_database_id"],
            "api_token": tool_parameters["cloudflare_api_token"],
        }

        # inchangé: on conserve la sélection du rôle (assistant ou user) depuis l'UI
        conversation_id = tool_parameters["conversation_id"]
        role = tool_parameters["role"]
        text = tool_parameters["text"]
        parent_message_id = tool_parameters.get("parent_message_id")

        # nouveau: tags optionnels sur le message
        tags = _normalize_tags(tool_parameters.get("tags"))

        # permettre de recevoir un metadata existant et y fusionner les tags
        metadata = tool_parameters.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}

        existing_tags = _normalize_tags(metadata.get("tags"))
        # fusion unique add-if-not-exist
        merged = existing_tags + _normalize_tags([t for t in tags if t.lower() not in {et.lower() for et in existing_tags}])
        if merged:
            metadata["tags"] = merged

        result = conversation_storage_put_message(
            db_brand=db_brand,
            db_metadata=db_metadata,
            conversation_id=conversation_id,
            role=role,
            text=text,
            parent_message_id=parent_message_id,
            metadata=metadata if metadata else None,
        )

        yield ToolInvokeMessage(text=json.dumps(result))
