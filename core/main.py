from core import (
    initialize_database,
    conversation_storage_put_message,
    conversation_storage_get_conversation,
    conversation_storage_get_conv_xml_basic,
)
from dotenv import load_dotenv
import time
import json

load_dotenv()

db_brand = "cloudflare_d1_lite"
db_metadata = {
    "account_id": "***REMOVED***",
    "database_id": "***REMOVED***",
    "api_token": "***REMOVED***",
}


def print_json(data):
    print(json.dumps(data, indent=2))


print("Initializing database...")
start_time = time.time()
init_result = initialize_database(db_brand, db_metadata)
print(f"Database initialization took {time.time() - start_time:.2f} seconds\n")

try:
    print("Testing conversation and message creation...")
    # Test put first message
    result1 = conversation_storage_put_message(
        db_brand,
        db_metadata,
        conversation_id=time.time(),
        role="user",
        text=f"Hello! {time.time()}",
    )
    print("\nFirst message result:")
    print_json(result1)

    # Test put second message
    result2 = conversation_storage_put_message(
        db_brand,
        db_metadata,
        conversation_id=result1["conversation_id"],
        role="assistant",
        text=f"Hi! How can I help? Now is {time.time()}",
        parent_message_id=result1["message_id"],
    )
    print(f"Second message result: {result2}")

    # Test get conversation
    print(f"\nRetrieving conversation...{result1['conversation_id']}")
    conversation = conversation_storage_get_conversation(
        db_brand, db_metadata, result1["conversation_id"]
    )
    print(f"\n+++++++++\n{str(conversation.messages)}\n+++++++++")
    if conversation and hasattr(conversation, "messages"):
        print(f"\nConversation {conversation.conversation_id}:")
        for msg in conversation.messages:
            print(f"[{msg.timestamp}] {msg.role}: {msg.text}")
    conv_xml = conversation_storage_get_conv_xml_basic(
        db_brand, db_metadata, result1["conversation_id"]
    )
    print(f"\nConversation XML:\n{conv_xml}")
except Exception as e:
    print(f"Error occurred: {str(e)}")
