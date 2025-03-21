from collections.abc import Generator
from typing import Any

from utils.core import conversation_storage_init_create_tables

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

class InitTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        db_brand = "cloudflare_d1_lite"
        db_metadata = {
            "account_id": tool_parameters["cloudflare_account_id"],
            "database_id": tool_parameters["cloudflare_d1_database_id"],
            "api_token": tool_parameters["cloudflare_api_token"],
        }
        init_result = conversation_storage_init_create_tables(db_brand, db_metadata)
        yield self.create_json_message(init_result)
