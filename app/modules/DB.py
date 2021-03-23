import json
import os
import sys
import warnings

from typing import Dict, List, Any

sys.path.append(os.getcwd())


from database.database import ChatStateDB


async def get_conversation(db: ChatStateDB, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    user_stats = db.fetch_user_messages(user_id=user_id, limit=limit)

    if not user_stats:
        return []

    return user_stats


async def get_messages(db: ChatStateDB, limit: int = 300) -> List[Dict[str, Any]]:
    messages = db.fetch_all_messages(limit=limit)

    if not messages:
        return []

    return messages


async def modify_message(db: ChatStateDB, id: int, select_intent: str):
    result = db.modify_chat_state(id, select_intent)

    return result


async def get_users(db: ChatStateDB, limit: int = 100) -> List[Dict[str, Any]]:
    users = db.fetch_users(limit=limit)

    if not users:
        return []

    return users
