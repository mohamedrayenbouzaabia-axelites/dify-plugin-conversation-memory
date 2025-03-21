from collections.abc import Generator
from typing import Any

from utils.core import conversation_storage_get_conv_xml_basic

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class GetConversationTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        db_brand = "cloudflare_d1_lite"
        db_metadata = {
            "account_id": tool_parameters["cloudflare_account_id"],
            "database_id": tool_parameters["cloudflare_d1_database_id"],
            "api_token": tool_parameters["cloudflare_api_token"],
        }
        conversation_id = tool_parameters["conversation_id"]
        max_round = tool_parameters.get("max_round", 10)
        user_input = tool_parameters.get("user_input")
        
        # 获取XML格式的对话
        xml_content = conversation_storage_get_conv_xml_basic(
            db_brand=db_brand,
            db_metadata=db_metadata,
            conversation_id=conversation_id,
            max_round=max_round,
        )
        xml_content = f"<history>\n{xml_content}\n</history>"
        
        # 如果有用户输入，在XML末尾添加一个message元素
        if user_input:
            user_message_xml = f"""<latest><message>
    <role>user</role>
    <content>{user_input}</content>
</message></latest>"""
            xml_content = f"{xml_content}\n{user_message_xml}"
        
        # 直接返回XML字符串
        yield self.create_text_message(xml_content)
