# Diwali Telegram Bot Configuration

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Bot Credentials ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# MongoDB URI (Leave empty to use built-in local JSON database for easy testing)
MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = os.getenv("DB_NAME", "diwali_bot")

# Admin Telegram User IDs (comma-separated in env e.g. "12345678,87654321")
OWNER_ID = int(os.getenv("OWNER_ID", "8055084559"))

ADMIN_IDS = [
    int(x.strip()) 
    for x in os.getenv("ADMIN_IDS", f"{OWNER_ID},5852353173").split(",") 
    if x.strip().isdigit() and int(x.strip()) != 0
]
if OWNER_ID not in ADMIN_IDS:
    ADMIN_IDS.insert(0, OWNER_ID)

# --- Economy & Rewards ---
DAILY_COINS = int(os.getenv("DAILY_COINS", "5000"))
DEFAULT_LOOT_COINS = int(os.getenv("LOOT_COINS", "10000"))
DIYA_MIN_COINS = 200
DIYA_MAX_COINS = 600

# --- Default Cooldowns (in seconds or hours) ---
DAILY_COOLDOWN_HOURS = 0.1
DEFAULT_LOOT_COOLDOWN_HOURS = 0.1

DIYA_COOLDOWN_SECONDS = 10       # 1 minute
MITHAI_COOLDOWN_SECONDS = 10     # 45 seconds
WISH_COOLDOWN_SECONDS = 10       # 30 seconds
DIWALI_COOLDOWN_SECONDS = 20     # 20 seconds

# --- Group Activity Thresholds ---
DEFAULT_MIN_GROUP_MESSAGES = 10   # Min messages before random event can trigger
RANDOM_DROP_CHANCE = 0.5         # 50% chance when threshold met (either interactive drop or aesthetic burst)

# --- High Quality Festive Image URLs ---
IMAGE_URLS = {
    "welcome": "https://images.unsplash.com/photo-1605649487212-47bdab064df8?auto=format&fit=crop&w=1200&q=80",
    "diya": [
        "https://files.catbox.moe/n1vqjb.png",
        "https://files.catbox.moe/h2257b.png",
        "https://files.catbox.moe/0v0oqa.png",
        "https://files.catbox.moe/c5pg3k.png"
    ],
    "diwali": [
        "https://files.catbox.moe/2zkngi.png", 
    ],
    "wish": [
        "https://files.catbox.moe/lb0n6q.png",
    ],
    "bomb": [
        "https://files.catbox.moe/9o3lym.png",
        "https://files.catbox.moe/9o3lym.png"
    ],
    "fireworks": [
        "https://files.catbox.moe/2ewz4u.png",
        "https://files.catbox.moe/2ewz4u.png"
    ],
    "mithai": [
        "https://files.catbox.moe/836ys4.png",
        "https://files.catbox.moe/836ys4.png",
        "https://files.catbox.moe/836ys4.png"
    ],
    "loot_drop": [
        "https://files.catbox.moe/c6re20.png",
        "https://files.catbox.moe/c6re20.png"
    ],
    "daily": "https://files.catbox.moe/c6re20.png",
    "loot": "https://files.catbox.moe/c6re20.png"
}

# --- Gifts Catalogue (Gifts cost coins and can be gifted to friends) ---
GIFTS = {
    "ladoo": {
        "id": "ladoo",
        "name": "Motichoor Ladoo",
        "emoji": "🟡",
        "price": 1000,
        "description": "Sweet melt-in-mouth Boondi Ladoo for festive luck!",
        "image": "https://files.catbox.moe/836ys4.png"
    },
    "kaju_katli": {
        "id": "kaju_katli",
        "name": "Kaju Katli Box",
        "emoji": "✨",
        "price": 2500,
        "description": "Royal silver-coated diamond cashew sweet!",
        "image": "https://files.catbox.moe/836ys4.png"
    },
    "phuljhadi": {
        "id": "phuljhadi",
        "name": "Electric Sparklers",
        "emoji": "🎇",
        "price": 5000,
        "description": "Glittering golden sparklers that sparkle bright!",
        "image": "https://files.catbox.moe/rhjmcc.png"
    },
    "anar": {
        "id": "anar",
        "name": "Golden Flowerpot Anar",
        "emoji": "🌋",
        "price": 8000,
        "description": "Shoots up a fountain of 10-foot golden sparkles!",
        "image": "https://files.catbox.moe/xvd322.png"
    },
    "rocket_box": {
        "id": "rocket_box",
        "name": "Mega Rocket Pack",
        "emoji": "🚀",
        "price": 12000,
        "description": "Whistles straight up to the sky with multi-color blasts!",
        "image": "https://files.catbox.moe/0mkl9h.png"
    },
    "laxmi_bomb": {
        "id": "laxmi_bomb",
        "name": "Laxmi Bomb & Sutli",
        "emoji": "💣",
        "price": 20000,
        "description": "Ear-shattering festive blast that shakes the ground!",
        "image": "https://files.catbox.moe/kmqxqw.png"
    },
    "gold_coin": {
        "id": "gold_coin",
        "name": "Shubh Laxmi Gold Coin",
        "emoji": "🪙",
        "price": 50000,
        "description": "Pure 24k Shubh Shagun coin for wealth & prosperity!",
        "image": "https://files.catbox.moe/tlglab.png"
    }
}

