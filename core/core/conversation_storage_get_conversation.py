from typing import Optional, List
import json
from connector import d1_executor
from .conversation_storage_dataclasses import Conversation, Message
from datetime import datetime

def conversation_storage_get_conversation(conversation_id: str, message_id: Optional[str] = 'latest', max_round: int = 10) -> Optional[Conversation]:
    """
    Retrieve message history for a specific conversation.

    Args:
        conversation_id: Target conversation ID
        message_id: Optional starting message ID. Default 'latest' gets the most recent messages.
                   Can be used to trace history from a specific message.
        max_round: Maximum number of message rounds to return (for lazy loading optimization)

    Returns:
        Conversation object containing message history (Message list).
        Message list structure depends on Conversation sequence type ('sequential' or 'tree').
        Returns None if conversation not found.
    """
    sql_conversation = "SELECT * FROM Conversation WHERE conversation_id = ?;"
    conversation_result = d1_executor(sql_conversation, f'["{conversation_id}"]')
    
    # Extract result from D1 response
    if not conversation_result.get('success'):
        return None
    
    results = conversation_result.get('metadata', {}).get('result', [{}])[0].get('results', [])
    if not results:
        return None
    
    conversation_row = results[0]
    
    conversation = Conversation(
        conversation_id=conversation_row['conversation_id'],
        project=conversation_row['project'],
        brand=conversation_row['brand'],
        sequence=conversation_row['sequence'],
        status=conversation_row['status'],
        created_at=datetime.fromisoformat(conversation_row['created_at']),
        latest_message_id=conversation_row['latest_message_id'],
        metadata=json.loads(conversation_row['metadata']) if conversation_row['metadata'] else None
    )

    message_list: List[Message] = []
    if conversation.sequence == 'sequential':
        sql_messages = """
        SELECT * FROM Message
        WHERE conversation_id = ?
        ORDER BY timestamp DESC
        LIMIT ?;
        """
        messages_result = d1_executor(sql_messages, f'["{conversation_id}", {max_round}]')
        
        # Extract messages from D1 response
        if messages_result.get('success'):
            message_rows = messages_result.get('metadata', {}).get('result', [{}])[0].get('results', [])
            
            for row in message_rows:
                message = Message(
                    message_id=row['message_id'],
                    conversation_id=row['conversation_id'],
                    role=row['role'],
                    text=row['text'],
                    parent_message_id=row['parent_message_id'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    metadata=json.loads(row['metadata']) if row['metadata'] else None
                )
                message_list.append(message)
        conversation.messages = list(reversed(message_list))

    elif conversation.sequence == 'tree':
        sql_messages = """
        SELECT * FROM Message
        WHERE conversation_id = ?
        ORDER BY timestamp ASC
        LIMIT ?;
        """
        messages_result = d1_executor(sql_messages, f'["{conversation_id}", {max_round}]')
        
        # Extract messages from D1 response
        if messages_result.get('success'):
            message_rows = messages_result.get('metadata', {}).get('result', [{}])[0].get('results', [])
            
            for row in message_rows:
                message = Message(
                    message_id=row['message_id'],
                    conversation_id=row['conversation_id'],
                    role=row['role'],
                    text=row['text'],
                    parent_message_id=row['parent_message_id'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    metadata=json.loads(row['metadata']) if row['metadata'] else None
                )
                message_list.append(message)
        conversation.messages = message_list

    else:
        conversation.messages = []

    return conversation


if __name__ == "__main__":
    conversation_id_to_get = "test-conversation-1" # 替换为你要获取的 conversation_id

    # 假设 conversation_id_to_get 的对话已经存在消息

    conversation_history = conversation_storage_get_conversation(conversation_id=conversation_id_to_get, max_round=5)

    if conversation_history:
        print(f"Conversation ID: {conversation_history.conversation_id}, Sequence: {conversation_history.sequence}")
        if hasattr(conversation_history, 'messages') and conversation_history.messages: # Check if messages attribute exists and is not empty
            print("Messages:")
            for message in conversation_history.messages:
                print(f"  - Role: {message.role}, Text: {message.text}, Timestamp: {message.timestamp}, Parent: {message.parent_message_id}")
        else:
            print("No messages found for this conversation.")
    else:
        print(f"Conversation with ID '{conversation_id_to_get}' not found.")