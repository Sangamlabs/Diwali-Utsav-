import random
from datetime import datetime, timedelta
from typing import Optional, Union, Tuple
from telegram import User, Update
from telegram.ext import ContextTypes
import config
from database import db

# Dynamic admin cache
_CUSTOM_ADMINS_CACHE = None

def is_owner(user_id: int) -> bool:
    """Check if user_id is the primary Bot Owner."""
    owner_id = getattr(config, "OWNER_ID", config.ADMIN_IDS[0] if config.ADMIN_IDS else 0)
    return user_id == owner_id

def is_admin(user_id: int) -> bool:
    """Check if user_id is the primary owner, permanent admin, or dynamic custom admin."""
    if is_owner(user_id):
        return True
    if user_id in config.ADMIN_IDS:
        return True
    if _CUSTOM_ADMINS_CACHE and user_id in _CUSTOM_ADMINS_CACHE:
        return True
    return False

async def init_admins_cache():
    """Load dynamic admins from DB into cache."""
    global _CUSTOM_ADMINS_CACHE
    if _CUSTOM_ADMINS_CACHE is None:
        _CUSTOM_ADMINS_CACHE = await db.get_setting("custom_admins", [])
    return _CUSTOM_ADMINS_CACHE

async def add_dynamic_admin(user_id: int) -> bool:
    """Add a new admin to the database and cache."""
    global _CUSTOM_ADMINS_CACHE
    if _CUSTOM_ADMINS_CACHE is None:
        _CUSTOM_ADMINS_CACHE = await db.get_setting("custom_admins", [])
    if user_id not in _CUSTOM_ADMINS_CACHE and user_id not in config.ADMIN_IDS:
        _CUSTOM_ADMINS_CACHE.append(user_id)
        await db.set_setting("custom_admins", _CUSTOM_ADMINS_CACHE)
        return True
    return False

async def remove_dynamic_admin(user_id: int) -> bool:
    """Remove a dynamic admin."""
    global _CUSTOM_ADMINS_CACHE
    if _CUSTOM_ADMINS_CACHE is None:
        _CUSTOM_ADMINS_CACHE = await db.get_setting("custom_admins", [])
    if user_id in _CUSTOM_ADMINS_CACHE:
        _CUSTOM_ADMINS_CACHE.remove(user_id)
        await db.set_setting("custom_admins", _CUSTOM_ADMINS_CACHE)
        return True
    return False

async def get_all_admins() -> list:
    """Get combined list of permanent owners and dynamic admins."""
    global _CUSTOM_ADMINS_CACHE
    if _CUSTOM_ADMINS_CACHE is None:
        _CUSTOM_ADMINS_CACHE = await db.get_setting("custom_admins", [])
    return list(set(config.ADMIN_IDS + _CUSTOM_ADMINS_CACHE))

def get_mention(user: Union[User, dict], custom_title: Optional[str] = None) -> str:
    """Generate HTML mention string for a user."""
    if isinstance(user, User):
        user_id = user.id
        name = custom_title or user.first_name or "Friend"
    else:
        user_id = user.get("user_id")
        name = custom_title or user.get("first_name") or "Friend"
    
    # Escape HTML special chars in name
    clean_name = str(name).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<a href="tg://user?id={user_id}">{clean_name}</a>'

def format_number(num: Union[int, float]) -> str:
    """Format numbers with comma separation."""
    return f"{int(num):,}"

# Cache for custom admin images
_CUSTOM_IMAGES_CACHE = None

VALID_IMAGE_CATEGORIES = [
    "diya",
    "diwali",
    "wish",
    "mithai",
    "bomb",
    "fireworks",
    "loot_drop",
    "welcome",
    "daily",
    "loot"
]

async def get_category_images(category: str) -> list:
    """Fetch images list for category (custom DB images priority, fallback to config)."""
    global _CUSTOM_IMAGES_CACHE
    if _CUSTOM_IMAGES_CACHE is None:
        _CUSTOM_IMAGES_CACHE = await db.get_setting("custom_images", {})

    custom_list = _CUSTOM_IMAGES_CACHE.get(category)
    if custom_list:
        return custom_list if isinstance(custom_list, list) else [custom_list]

    default = config.IMAGE_URLS.get(category, [])
    return default if isinstance(default, list) else [default]

def get_random_image(category: str) -> str:
    """Fetch a random image URL/file_id for category (checks cache or config)."""
    global _CUSTOM_IMAGES_CACHE
    if _CUSTOM_IMAGES_CACHE and category in _CUSTOM_IMAGES_CACHE:
        val = _CUSTOM_IMAGES_CACHE[category]
        if isinstance(val, list) and val:
            return random.choice(val)
        elif isinstance(val, str) and val:
            return val

    img_data = config.IMAGE_URLS.get(category)
    if isinstance(img_data, list) and img_data:
        return random.choice(img_data)
    elif isinstance(img_data, str) and img_data:
        return img_data
    return config.IMAGE_URLS.get("welcome", "")

async def add_custom_image(category: str, image_item: str) -> int:
    """Add an image URL or Telegram file_id to a category."""
    global _CUSTOM_IMAGES_CACHE
    if _CUSTOM_IMAGES_CACHE is None:
        _CUSTOM_IMAGES_CACHE = await db.get_setting("custom_images", {})

    if category not in _CUSTOM_IMAGES_CACHE or not isinstance(_CUSTOM_IMAGES_CACHE[category], list):
        # Initialize from config or empty
        base = config.IMAGE_URLS.get(category, [])
        _CUSTOM_IMAGES_CACHE[category] = list(base) if isinstance(base, list) else ([base] if base else [])

    if image_item not in _CUSTOM_IMAGES_CACHE[category]:
        _CUSTOM_IMAGES_CACHE[category].append(image_item)

    await db.set_setting("custom_images", _CUSTOM_IMAGES_CACHE)
    return len(_CUSTOM_IMAGES_CACHE[category])

async def remove_custom_image(category: str, index: int) -> bool:
    """Remove image by 1-based index."""
    global _CUSTOM_IMAGES_CACHE
    if _CUSTOM_IMAGES_CACHE is None:
        _CUSTOM_IMAGES_CACHE = await db.get_setting("custom_images", {})

    if category in _CUSTOM_IMAGES_CACHE and isinstance(_CUSTOM_IMAGES_CACHE[category], list):
        if 0 <= index < len(_CUSTOM_IMAGES_CACHE[category]):
            _CUSTOM_IMAGES_CACHE[category].pop(index)
            await db.set_setting("custom_images", _CUSTOM_IMAGES_CACHE)
            return True
    return False

async def reset_custom_images(category: Optional[str] = None):
    """Reset category or all images to config defaults."""
    global _CUSTOM_IMAGES_CACHE
    if _CUSTOM_IMAGES_CACHE is None:
        _CUSTOM_IMAGES_CACHE = await db.get_setting("custom_images", {})

    if category:
        if category in _CUSTOM_IMAGES_CACHE:
            del _CUSTOM_IMAGES_CACHE[category]
    else:
        _CUSTOM_IMAGES_CACHE = {}

    await db.set_setting("custom_images", _CUSTOM_IMAGES_CACHE)

def check_cooldown(last_time_iso: Optional[str], cooldown_seconds: int) -> Tuple[bool, int]:
    """
    Check if cooldown has expired.
    Returns (is_ready: bool, remaining_seconds: int)
    """
    if not last_time_iso:
        return True, 0
    try:
        last_dt = datetime.fromisoformat(last_time_iso)
        diff = (datetime.utcnow() - last_dt).total_seconds()
        remaining = cooldown_seconds - diff
        if remaining <= 0:
            return True, 0
        return False, int(remaining)
    except Exception:
        return True, 0

def format_remaining_time(seconds: int) -> str:
    """Format remaining seconds into human readable string e.g. '5h 23m 12s'."""
    if seconds <= 0:
        return "now"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    return " ".join(parts)

async def resolve_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Tuple[Optional[int], Optional[str]]:
    """
    Resolve target user from:
    1. Reply message
    2. Command argument (@username or numeric user_id)
    Returns (target_id, target_name)
    """
    message = update.effective_message
    if not message:
        return None, None

    # Case 1: Reply
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
        if target.is_bot:
            return None, "Bots cannot celebrate with gifts or sweets! Please select a real user."
        return target.id, target.first_name

    # Case 2: Argument
    if context.args and len(context.args) > 0:
        arg = context.args[0].strip()
        # Direct numeric ID
        if arg.isdigit():
            target_id = int(arg)
            target_user = await db.get_user(target_id)
            target_name = target_user.get("first_name", f"User {target_id}")
            return target_id, target_name
        
        # Username tag
        if arg.startswith("@"):
            uname = arg[1:].lower()
            # Look up in database
            all_users = await db.get_all_users()
            for u in all_users:
                if (u.get("username") or "").lower() == uname:
                    return u["user_id"], u.get("first_name", arg)
            return None, f"User {arg} hasn't started the bot or joined yet."

    return None, None

