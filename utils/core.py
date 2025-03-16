from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

from data_connector import (
    get_conversation,
    get_conversation_by_message,
    put_conversation,
    put_message,
    get_messages,
)


@dataclass
class Conversation:
    """
    表示一个对话会话的类。

    Attributes:
        conversation_id (str): 对话ID，作为唯一标识符 (主键).  类型为 TEXT 在数据库中。
                                 如果未提供，则自动生成 UUID。
        project (Optional[str]): 项目标识符，用于区分不同项目的对话。 类型为 TEXT 在数据库中。
                                 可选字段。
        brand (Optional[str]): 品牌标识符，用于进一步区分。 类型为 TEXT 在数据库中。
                                 可选字段。
        sequence (str): 对话序列类型，默认为 'sequential' (顺序对话)。
                        可以设置为 'sequential' (顺序对话) 或 'tree' (树状对话，支持编辑/重试等，允许父消息有多个子消息)。
                        类型为 TEXT 在数据库中，默认值为 'sequential'，非空约束。
        status (str): 对话状态，默认为 'active'。例如，可以是 'active' (活跃) 或 'archived' (已存档)。
                      类型为 TEXT 在数据库中，默认值为 'active'，非空约束。
        created_at (datetime): 对话创建的时间戳，默认为当前时间。 类型为 DATETIME 在数据库中，默认为当前时间戳。
        latest_message_id (Optional[str]): 最新消息的ID，用于快速访问最新消息。 类型为 TEXT 在数据库中。
                                            可选字段，通常在对话中有新消息时更新。
        metadata (Optional[Dict[str, Any]]):  与对话相关的元数据，可以存储任何额外的信息，以字典形式存储。
                                            类型为 TEXT 在数据库中，这里我们使用 Python 字典来表示更结构化的数据，方便使用。
    """

    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project: Optional[str] = None
    brand: Optional[str] = None
    sequence: str = field(default="sequential")
    status: str = field(default="active")
    created_at: datetime = field(default_factory=datetime.now)
    latest_message_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Message:
    """
    表示对话中的一条消息的类。

    Attributes:
        conversation_id (str):  所属对话的ID，外键，关联到 Conversation 表的 conversation_id。 类型为 TEXT 在数据库中，非空约束。
        role (str): 消息发送者的角色，例如 'user' (用户), 'assistant' (助手), 'system' (系统) 等。 类型为 TEXT 在数据库中。
        text (str): 消息的文本内容，不能为空。 类型为 TEXT 在数据库中，非空约束。
        message_id (str): 消息ID，作为唯一标识符 (主键)。 类型为 TEXT 在数据库中。
                             如果未提供，则自动生成 UUID。
        parent_message_id (Optional[str]): 父消息ID，用于表示消息的层级关系，例如回复消息或编辑/重试的消息。 可以为空。
                                        类型为 TEXT 在数据库中，这里使用 Optional[str] 表示可以为空。
                                        关联到 Message 表自身的 message_id (自引用外键关系).
        timestamp (datetime): 消息创建的时间戳，默认为当前时间。 类型为 DATETIME 在数据库中，默认为当前时间戳。
        metadata (Optional[Dict[str, Any]]): 与消息相关的元数据，可以存储任何额外的信息，以字典形式存储。
                                            类型为 TEXT 在数据库中，这里我们使用 Python 字典来表示更结构化的数据，方便使用。
    """

    conversation_id: str
    role: str
    text: str
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_message_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None


def create_conversation(
    conversation_id: Optional[str] = None,
    project: Optional[str] = None,
    brand: Optional[str] = None,
    sequence: str = "sequential",
    status: str = "active",
    metadata: Optional[Dict[str, Any]] = None,
) -> Conversation:
    """
    创建并返回一个新的 Conversation 对象。

    Args:
        conversation_id (Optional[str]):  对话ID，如果提供则使用，否则自动生成 UUID。
        project (Optional[str]): 项目标识符，可选。
        brand (Optional[str]): 品牌标识符，可选。
        sequence (str): 对话序列类型 ('sequential' 或 'tree')，默认为 'sequential'。
        status (str): 对话状态，默认为 'active'。
        metadata (Optional[Dict[str, Any]]):  对话元数据，可选。

    Returns:
        Conversation: 创建的 Conversation 对象。
    """
    sql_execute = put_conversation(
        conversation_id=conversation_id,
        project=project,
        brand=brand,
        sequence=sequence,
        status=status,
        metadata=metadata,
    )
    if not sql_execute.success:
        raise ValueError(f"Failed to create conversation with ID {conversation_id}.")
    return sql_execute


def create_message(
    role: str,
    text: str,
    conversation_id: Optional[str],
    message_id: Optional[str] = None,
    parent_message_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Message:
    """
    创建并返回一个新的 Message 对象。

    Args:
        conversation_id (str): 所属对话的ID。
        role (str): 消息发送者的角色。
        text (str): 消息的文本内容。
        message_id (Optional[str]): 消息ID，如果提供则使用，否则自动生成 UUID。
        parent_message_id (Optional[str]): 父消息ID，用于构建消息树，可选。
                                            如果为 None，则表示这是一条根消息或顺序对话中的下一条消息。
                                            切换为树状对话时，需要显式指定 parent_message_id 来建立消息之间的父子关系。
        metadata (Optional[Dict[str, Any]]): 消息元数据，可选。

    Returns:
        Message: 创建的 Message 对象。
    """
    if not conversation_id:
        conversation_id = create_conversation(brand="unknown").conversation_id
        # 通常, Dify 会提供一个对话的 ID, 但是不建议完全用: 建议加个后置参数, 节点的 ID 等, 用来实现细粒度的可调.
    if not message_id:
        message_id = str(uuid.uuid4())
        # message_id 则是和这里的 conversation 关联而已, 所以其实建议直接内部生成, 或者外部也可以.
        # TODO 得加个重复检查, 毕竟外部提供的话可不讲究那么多...
        # 但是, v 1.0.0 就先内置吧
    if not parent_message_id:
        parent_message_id = message_lookup_parent_by_conversation(conversation_id)
        if not parent_message_id:
            parent_message_id = message_id
    new_message = put_message(
        role=role,
        text=text,
        conversation_id=conversation_id,
        message_id=message_id,
        parent_message_id=parent_message_id,
        metadata=metadata,
    )
    success = new_message.success
    if not success:
        raise ValueError(f"Failed to create message with ID {message_id}.")
    return {
        "success": success,
        "conversation_id": conversation_id,
        "message_id": message_id,
        "metadata": "TBD",
    }


def message_lookup_conversation_by_message(message_id):
    """
    查找消息的函数，返回 conversation_id"
    """
    the_conversation = get_conversation_by_message(message_id)
    if the_conversation:
        return the_conversation.conversation_id
    else:
        raise ValueError(f"Message with ID {message_id} not found in any conversation.")


def message_lookup_parent_by_conversation(conversation_id):
    """
    查找消息的函数，返回 parent_message_id"
    """
    the_conversation = get_conversation(conversation_id)
    if the_conversation:
        return the_conversation.latest_message_id
    else:
        return None


# 反序列化, xml 版本. 接收参数 max_rounds, conversation_id.


def deserialize_conversation_xml(conversation_id, max_rounds):
    """
    反序列化对话的函数，返回对话的 XML 表示。
    """
    conversation = get_conversation(conversation_id)
    if conversation.sequence == "sequential":
        # 从 message 表里检索, 条件是 message.conversation_id == conversation_id, 以时间戳倒排, 取 max_rounds 条.
        # 然后, 生成正的 xml 格式的 message 对
        messages_raw = get_messages(conversation_id, max_rounds)
        """
        Example:
        <message>
            <role>user</role>
            <content>...</conetent>
        </message>
        <message>
            <role>assistant</role>
            <content>...</conetent>
        </message>
        again...        
        """
        messages_xml = ""
        for message in messages_raw:
            messages_xml += f"<message><role>{message.role}</role><content>{message.text}</content></message>"
        return messages_xml
