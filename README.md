## Dify Plugin — Conversation Memory

Store and retrieve conversation history for Dify apps using Cloudflare D1. This plugin exposes a small set of tools to persist messages, fetch a conversation (as XML or JSON), and tag conversations for later retrieval.

Key features
- Cloudflare D1–backed storage (lightweight, serverless)
- Tools: Store Message, Load Conversation, Put Conversation Tag
- Basic XML or JSON conversation export for LLM-friendly prompting
- Auto-creates Conversation and Message tables on first run

What this is not
- A full-blown vector memory. It’s a simple, durable conversation log with optional tags.

Requirements
- Python 3.12
- Cloudflare Account with D1 Database
- Cloudflare API Token with D1 read/write permission

Quick start (local debug)
1) Install deps: `cd data_function_conversation_memory && pip install -r requirements.txt`
2) Configure remote debug (optional): copy `data_function_conversation_memory/.env.example` to `.env` and set `INSTALL_METHOD=remote`, `REMOTE_INSTALL_URL`, and `REMOTE_INSTALL_KEY` from your Dify instance.
3) Run: `python -m main` from `data_function_conversation_memory/`. The plugin registers with your Dify instance in debug mode.

Using in Dify
- Install the plugin and set provider credentials:
  - `cloudflare_account_id`
  - `cloudflare_d1_database_id`
  - `cloudflare_api_token`
- Add tools to your workflow/agent as needed:
  - `Store Message` (`put_message`): append a user/assistant message to a conversation; optional tags merged into message metadata.
  - `Load Conversation` (`get_conversation`): fetch history as XML (default) or JSON; can append current user input.
  - `Put Conversation Tag` (`put_conversation_tag`): add unique tags to Conversation.metadata.tags (CSV string stored).

Credentials and environment
- In Dify: set provider credentials above.
- For direct connector usage outside the tools (e.g., `utils/connector/cloudflare_d1_lite.py:d1_executor`), the following environment variables are read:
  - `CF_ACCOUNT_ID`, `CF_DATABASE`, `CF_API_TOKEN`

Database schema (Cloudflare D1)
- Conversation
  - `conversation_id TEXT PRIMARY KEY`, `project TEXT`, `brand TEXT`, `sequence TEXT DEFAULT 'sequential'`, `status TEXT DEFAULT 'active'`, `created_at DATETIME DEFAULT CURRENT_TIMESTAMP`, `latest_message_id TEXT`, `metadata TEXT (JSON)`
- Message
  - `message_id TEXT PRIMARY KEY`, `conversation_id TEXT`, `role TEXT`, `text TEXT`, `parent_message_id TEXT`, `timestamp DATETIME DEFAULT CURRENT_TIMESTAMP`, `metadata TEXT (JSON)`

Project layout
- `data_function_conversation_memory/manifest.yaml` — Plugin manifest
- `data_function_conversation_memory/provider/` — Provider config and validation
- `data_function_conversation_memory/tools/` — Tool definitions (YAML + Python)
- `data_function_conversation_memory/utils/` — Core logic and DB connector
- `data_function_conversation_memory/main.py` — Plugin entrypoint

Packaging
- From repository root: `dify-plugin plugin package ./data_function_conversation_memory`
- Produces a `plugin.difypkg` suitable for Marketplace or self-hosted install.

Notes and limitations
- Storage backend is Cloudflare D1 only.
- Message `text` is stored as a JSON-encoded string; consumer code should treat it as plain text when reading.
- XML output is intentionally simple; escape/transform as needed for your prompts.
- Tags are stored CSV-style in metadata (case-insensitive dedupe).

Support / Issues
- Open issues at: https://github.com/alterxyz/dify-plugin-conversation-memory/issues/new/choose
