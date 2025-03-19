# 对话系统数据模型 - `Conversation` 和 `Message`

本项目定义了 `Conversation` 和 `Message` 两个 Python `dataclass`，用于构建对话系统的数据模型。

## `Conversation` 类

`Conversation` 类用于表示一个对话会话。

**设计目标:**

* **唯一标识对话:**  每个对话都有唯一的 `conversation_id` 作为主键。
* **支持项目和品牌分类:**  `project` 和 `brand` 字段用于对话的分类和组织，例如区分不同项目或品牌下的对话。 `brand` 字段的用途非常灵活，可以根据具体应用场景进行定义，例如用作标签或更细粒度的分类。
* **支持顺序和树状对话序列:**  通过 `sequence` 字段，支持两种对话序列类型：
    * **`sequential` (顺序对话):**  消息线性排列，按时间顺序倒序检索，适用于简单的线性对话场景。
    * **`tree` (树状对话):**  消息通过 `parent_message_id` 形成树状结构，支持消息的编辑和重试功能。 这是为了实现 AI Chatbot 的 retry/edit 功能而设计的。
* **记录对话状态:**  `status` 字段用于表示对话的当前状态，例如 `'active'` (活跃) 或 `'archived'` (已存档)。 目前主要关注 `'active'` 状态，`'archived'` 等状态和数据归档处理是未来的扩展方向。
* **记录创建时间:**  `created_at` 字段记录对话的创建时间戳。
* **快速访问最新消息:**  `latest_message_id` 字段指向最新消息的 ID，用于快速访问最新消息，优化性能。
* **灵活的元数据存储:**  `metadata` 字段是一个字典，用于存储与对话相关的任何额外信息。  数据库中以 JSON 格式存储，Python 中使用字典方便操作。  `metadata` 的具体用途由开发者根据实际需求灵活定义，例如存储对话摘要、用户偏好、会话标签、使用的模型配置等。

**字段:**

* `conversation_id`: 对话 ID (主键, TEXT, UUID 自动生成).
* `project`: 项目标识符 (TEXT, 可选).
* `brand`: 品牌标识符 (TEXT, 可选, 用途自定义).
* `sequence`: 对话序列类型 (TEXT, 默认 'sequential', 非空, 可选 'sequential' 或 'tree').
* `status`: 对话状态 (TEXT, 默认 'active', 非空, 目前仅考虑 'active').
* `created_at`: 创建时间戳 (DATETIME, 默认当前时间).
* `latest_message_id`: 最新消息 ID (TEXT, 可选).
* `metadata`: 元数据 (TEXT/JSON, 可选, 字典类型, 用途自定义).

## `Message` 类

`Message` 类用于表示对话中的一条消息。

**设计目标:**

* **关联到所属对话:**  `conversation_id` 字段作为外键，关联到 `Conversation` 表，表示消息属于哪个对话。
* **记录消息发送者角色:**  `role` 字段表示消息的发送者角色，例如 'user', 'assistant', 'system' 等。 当用户编辑消息时，新的消息角色仍然是 'user'。
* **存储消息文本内容:**  `text` 字段存储消息的具体文本内容。
* **唯一标识消息:**  `message_id` 字段作为主键，唯一标识每条消息。
* **支持消息层级关系 (树状对话):**  `parent_message_id` 字段用于构建消息之间的层级关系，特别是在 `sequence='tree'` 的对话中。 用于实现消息编辑和重试功能。 当消息是编辑或重试后的新消息时，`parent_message_id` 指向被编辑或重试的原始消息的 `message_id`。
* **记录消息创建时间:**  `timestamp` 字段记录消息的创建时间戳。
* **灵活的元数据存储:**  `metadata` 字段是一个字典，用于存储与消息相关的任何额外信息。 数据库中以 JSON 格式存储，Python 中使用字典方便操作。 `metadata` 的具体用途由开发者根据实际需求灵活定义，例如存储消息发送/接收状态、tokens 消耗统计、外部引用链接、模型生成参数等。

**字段:**

* `conversation_id`: 所属对话 ID (TEXT, 外键, 非空).
* `role`: 消息发送者角色 (TEXT, 非空).
* `text`: 消息文本内容 (TEXT, 非空).
* `message_id`: 消息 ID (主键, TEXT, UUID 自动生成).
* `parent_message_id`: 父消息 ID (TEXT, 自引用外键, 可选, 用于树状对话).
* `timestamp`: 创建时间戳 (DATETIME, 默认当前时间).
* `metadata`: 元数据 (TEXT/JSON, 可选, 字典类型, 用途自定义).

## 函数签名 (待实现)

```python
def put_message(conversation_id: str, role: str, text: str, parent_message_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    向指定对话会话添加一条新消息。

    Args:
        conversation_id:  消息所属的对话 ID.
        role: 消息发送者角色 ('user', 'assistant', 'system' 等).
        text: 消息文本内容.
        parent_message_id: 可选的父消息 ID, 用于回复或编辑消息的场景.
        metadata: 可选的元数据字典.

    Returns:
        新创建的消息的 message_id.
    """
    pass # 待实现


def get_conversation(conversation_id: str, message_id: Optional[str] = 'latest', max_round: int = 10) -> Conversation:
    """
    获取指定对话会话的消息历史。

    Args:
        conversation_id: 要获取的对话 ID.
        message_id:  可选的起始消息 ID。 默认为 'latest'，获取最新的消息。 可以用于从特定消息开始向前追溯历史。
        max_round:  最大返回的消息轮数 (用于懒加载优化).

    Returns:
        Conversation 对象，包含指定对话的消息历史 (Message 列表).  消息列表的具体结构取决于 Conversation 的 sequence 类型 ('sequential' 或 'tree').
    """
    pass # 待实现