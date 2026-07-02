import random
import string
from schemas import Chats

def generate_random_string(length = 12):
    # Combines lowercase, uppercase, and digits (abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789)
    characters = string.ascii_letters + string.digits

    # Select characters randomly (allows duplicates)
    random_chars = random.choices(characters, k=length)

    return "".join(random_chars)

def format_chats(chats):
    return [
        Chats(
            role=chat.role,
            message=chat.message,
            model_used=chat.model_used,
            sent_on=chat.sent_on,
        )
        for chat in chats
    ]
    