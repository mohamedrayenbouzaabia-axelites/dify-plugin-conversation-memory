# python
# put_conversation_tag.py
from collections.abc import Generator
from typing import Any, List

from utils.core import conversation_storage_put_tag

from dify_plugin import Tool
import json

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

class PutConversationTagTool(Tool):
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
        

        conversation_id = tool_parameters["conversation_id"]
        tags = _normalize_tags(tool_parameters.get("tags") or tool_parameters.get("tag"))

        result = conversation_storage_put_tag(
            db_brand=db_brand,
            db_metadata=db_metadata,
            conversation_id=conversation_id,
            tags=tags,
        )
        yield self.create_json_message(result)
