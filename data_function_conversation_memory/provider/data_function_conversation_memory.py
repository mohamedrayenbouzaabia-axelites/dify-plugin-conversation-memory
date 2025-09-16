from typing import Any
from utils.core import initialize_database
from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError
from utils.connector.cloudflare_d1_lite import (
    cloudflare_token_verify,
    cloudflare_d1_query,
    cloudflare_d1_result_success,
)


class DataFunctionConversationMemoryProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            # Basic presence checks
            account_id = (credentials.get("cloudflare_account_id") or "").strip()
            database_id = (credentials.get("cloudflare_d1_database_id") or "").strip()
            api_token = (credentials.get("cloudflare_api_token") or "").strip()

            if not account_id:
                raise ToolProviderCredentialValidationError("cloudflare_account_id is required")
            if not database_id:
                raise ToolProviderCredentialValidationError("cloudflare_d1_database_id is required")
            if not api_token:
                raise ToolProviderCredentialValidationError("cloudflare_api_token is required")

            # Verify API token with Cloudflare
            token_check = cloudflare_token_verify(api_token)
            if not token_check.get("success"):
                # Include helpful error info if available
                err = token_check.get("error") or token_check
                raise ToolProviderCredentialValidationError(f"Invalid Cloudflare API token: {err}")

            # Simple D1 query to validate account/database access
            probe_sql = "SELECT 1 as ok;"
            probe = cloudflare_d1_query(
                account_id=account_id,
                database_id=database_id,
                api_token=api_token,
                sql_query=probe_sql,
                params="[]",
            )

            if not probe.get("success"):
                meta = probe.get("metadata", {})
                http_status = meta.get("http_status")
                detail = meta.get("detail") or meta
                raise ToolProviderCredentialValidationError(
                    f"Cloudflare D1 connection failed (HTTP {http_status}): {detail}"
                )

            if not cloudflare_d1_result_success(probe):
                raise ToolProviderCredentialValidationError(
                    "Cloudflare D1 query unsuccessful: insufficient permissions or invalid IDs"
                )
            initialize_database(db_brand, db_metadata)

        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
