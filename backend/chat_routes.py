"""DavidAI chat API helpers — conversation storage."""

from datetime import datetime

from flask_login import current_user

from backend.chat_service import (
    DEFAULT_CHAT_MODEL,
    build_davidai_system_prompt,
    chat_with_ollama,
    chat_with_search,
)
from backend.extensions import db
from database.models import Conversation, Message


def get_or_create_conversation(user_id: int) -> Conversation:
    conversation = db.session.scalar(
        db.select(Conversation)
        .filter_by(user_id=user_id)
        .order_by(Conversation.updated_at.desc())
    )
    if conversation is None:
        conversation = Conversation(user_id=user_id, title="DavidAI Chat")
        db.session.add(conversation)
        db.session.commit()
    return conversation


def get_user_conversation(user_id: int) -> Conversation | None:
    return db.session.scalar(
        db.select(Conversation)
        .filter_by(user_id=user_id)
        .order_by(Conversation.updated_at.desc())
    )


def get_message_history(conversation_id: int, limit: int = 20) -> list[dict]:
    messages = db.session.scalars(
        db.select(Message)
        .filter_by(conversation_id=conversation_id)
        .order_by(Message.created_at.asc())
    ).all()
    if limit:
        messages = messages[-limit:]
    return [{"role": m.role, "content": m.content} for m in messages]


def conversation_to_dict(conversation: Conversation) -> dict:
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "model": m.model,
                "search_mode": m.search_mode,
                "created_at": m.created_at.isoformat(),
            }
            for m in conversation.messages
        ],
    }


def process_chat_message(message: str, use_web_search: bool = False) -> dict:
    conversation = get_or_create_conversation(current_user.id)
    history = get_message_history(conversation.id)

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=message,
        model=DEFAULT_CHAT_MODEL,
        search_mode=use_web_search,
    )
    db.session.add(user_message)

    if use_web_search:
        result = chat_with_search(message, DEFAULT_CHAT_MODEL, history)
    else:
        system_prompt = build_davidai_system_prompt()
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})
        result = chat_with_ollama(messages, DEFAULT_CHAT_MODEL)

    if not result.get("ok"):
        db.session.rollback()
        return result

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=result["message"],
        model=result.get("model", DEFAULT_CHAT_MODEL),
        search_mode=use_web_search,
    )
    db.session.add(assistant_message)
    conversation.updated_at = datetime.utcnow()
    if len(history) == 0 and conversation.title == "DavidAI Chat":
        conversation.title = message[:80]
    db.session.commit()

    result["conversation_id"] = conversation.id
    return result


def clear_user_conversations(user_id: int) -> int:
    conversations = db.session.scalars(
        db.select(Conversation).filter_by(user_id=user_id)
    ).all()
    count = 0
    for conversation in conversations:
        count += len(conversation.messages)
        db.session.delete(conversation)
    db.session.commit()
    return count
