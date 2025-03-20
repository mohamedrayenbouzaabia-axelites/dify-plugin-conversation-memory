from typing import Optional, Dict, Any
import uuid
import json
from datetime import datetime
from connector import d1_executor
from .conversation_storage_dataclasses import Message, Conversation

def conversation_storage_put_message(conversation_id: str, role: str, text: str, parent_message_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Add a new message to a specific conversation.
    If the conversation doesn't exist, create it first.

    Args:
        conversation_id: Target conversation ID
        role: Message sender role ('user', 'assistant', 'system', etc.)
        text: Message content text
        parent_message_id: Optional parent message ID for replies or edits
        metadata: Optional metadata dictionary

    Returns:
        Newly created message ID
    """
    # Check if conversation exists
    sql_check = "SELECT conversation_id FROM Conversation WHERE conversation_id = ?;"
    check_result = d1_executor(sql_check, f'["{conversation_id}"]')
    check_data = check_result.get('metadata', {}).get('result', [{}])[0].get('results', [])
    
    # If conversation doesn't exist, create it
    if not check_data:
        conversation = Conversation(conversation_id=conversation_id)
        sql_create_conv = """
        INSERT INTO Conversation (conversation_id, sequence, status, created_at)
        VALUES (?, ?, ?, ?);
        """
        conv_values = f'["{conversation.conversation_id}", "{conversation.sequence}", "{conversation.status}", "{conversation.created_at.isoformat()}"]'
        d1_executor(sql_create_conv, conv_values)
    
    # Now create the message
    message_id = str(uuid.uuid4())
    timestamp = datetime.now()
    message = Message(
        conversation_id=conversation_id,
        role=role,
        text=text,
        message_id=message_id,
        parent_message_id=parent_message_id,
        timestamp=timestamp,
        metadata=metadata,
    )

    sql_message = """
    INSERT INTO Message (message_id, conversation_id, role, text, parent_message_id, timestamp, metadata)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """
    message_values = f'["{message.message_id}", "{message.conversation_id}", "{message.role}", "{message.text}", {json.dumps(message.parent_message_id)}, "{message.timestamp.isoformat()}", {json.dumps(json.dumps(message.metadata) if message.metadata else None)}]'
    d1_executor(sql_message, message_values)

    sql_conversation = """
    UPDATE Conversation
    SET latest_message_id = ?
    WHERE conversation_id = ?;
    """
    conversation_values = f'["{message.message_id}", "{message.conversation_id}"]'
    d1_executor(sql_conversation, conversation_values)

    return {
        "message_id" : message_id,
        "conversation_id" : conversation_id
    }

if __name__ == "__main__":
    # Example usage
    conversation_id_example = "test-conversation-1" # Replace with your conversation_id
    # Assume the conversation exists
    message_id = conversation_storage_put_message(
        conversation_id=conversation_id_example,
        role="user",
        text="Hello!",
        metadata={"source": "web"}
    )
    print(f"Message added with ID: {message_id}")

    message_id_reply = conversation_storage_put_message(
        conversation_id=conversation_id_example,
        role="assistant",
        text="Hello! How can I help you?",
        parent_message_id=message_id,
        metadata={"model": "v1.0"}
    )
    print(f"Reply message added with ID: {message_id_reply}")