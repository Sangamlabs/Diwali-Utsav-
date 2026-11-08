import random
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
import config
from database import db
from utils import (
    get_mention,
    format_number,
    get_random_image,
    check_cooldown,
    format_remaining_time,
    resolve_target_user
)

async def diya_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /diya command - Light a diya, receive festive blessing & coins."""
    user = update.effective_user
    if not user:
        return

    user_data = await db.get_user(user.id, {"username": user.username, "first_name": user.first_name})
    last_diya = user_data.get("last_diya")

    # Cooldown check
    is_ready, remaining = check_cooldown(last_diya, config.DIYA_COOLDOWN_SECONDS)
    if not is_ready:
        time_str = format_remaining_time(remaining)
        await update.effective_message.reply_text(
            f"🕯️ Your diya is glowing steadily, {get_mention(user)}!\n"
            f"Please wait <b>{time_str}</b> before lighting another diya. 🪔",
            parse_mode="HTML"
        )
        return

    # Reward random coins
    coins_reward = random.randint(config.DIYA_MIN_COINS, config.DIYA_MAX_COINS)
    new_balance = await db.add_coins(user.id, coins_reward)
    await db.update_user(user.id, {"last_diya": datetime.utcnow().isoformat()})

    # Record community diya in groups
    chat = update.effective_chat
    if chat and chat.type in ["group", "supergroup"]:
        from handlers.group_diya import record_group_diya
        await record_group_diya(chat.id, user.id, user.first_name, context)

    diya_quotes = [
        "May the divine light of Diwali illuminate your life with peace, prosperity, and happiness!",
        "With every diya lit, darkness vanishes and divine blessings arrive!",
        "Shubh Deepavali! May your home be filled with endless warmth and glowing joy!",
        "A holy diya is lit! Goddess Lakshmi showers her golden blessings upon you!"
    ]
    quote = random.choice(diya_quotes)
    img_url = get_random_image("diya")

    caption = (
        f"🪔 <b>DIVINE DIYA ILLUMINATED!</b> 🪔\n\n"
        f"✨ {get_mention(user)} has lit a sacred Diwali Diya!\n\n"
        f"<i>\"{quote}\"</i>\n\n"
        f"🪙 <b>Blessing Received:</b> +<code>{format_number(coins_reward)}</code> Coins\n"
        f"💰 <b>Total Balance:</b> <code>{format_number(new_balance)}</code> Coins\n\n"
        f"🕯️ <i>Next diya can be lit in {config.DIYA_COOLDOWN_SECONDS} seconds.</i>"
    )

    try:
        await update.effective_message.reply_photo(
            photo=img_url,
            caption=caption,
            parse_mode="HTML"
        )
    except Exception:
        await update.effective_message.reply_text(caption, parse_mode="HTML")

async def diwali_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /diwali command - Burst a random festive cracker."""
    user = update.effective_user
    if not user:
        return

    user_data = await db.get_user(user.id, {"username": user.username, "first_name": user.first_name})
    last_diwali = user_data.get("last_diwali")

    is_ready, remaining = check_cooldown(last_diwali, config.DIWALI_COOLDOWN_SECONDS)
    if not is_ready:
        time_str = format_remaining_time(remaining)
        await update.effective_message.reply_text(
            f"💨 Safe distance! Wait <b>{time_str}</b> before lighting another cracker! 🧨",
            parse_mode="HTML"
        )
        return

    await db.update_user(user.id, {"last_diwali": datetime.utcnow().isoformat()})

    crackers = [
        {
            "name": "Sutli Bomb",
            "sound": "💥💥 DHHHAAAAMMM-DHAAAMAKAA! 💥💥",
            "effect": "The ground trembled as the legendary Sutli Bomb detonated in high decibels!",
            "category": "bomb"
        },
        {
            "name": "Sky Shot Rocket",
            "sound": "🚀 WWHHHIIIISSSSTTTLLLEEE... 🎆 KABOOM! 🎆",
            "effect": "A dazzling red-green peony flower burst 200 feet into the night sky!",
            "category": "fireworks"
        },
        {
            "name": "Golden Anar (Flowerpot)",
            "sound": "🌋 SHHHHSSSSSHHHHHH... ✨✨✨✨",
            "effect": "A 15-foot shower of bright golden and silver sparkles lit up the entire street!",
            "category": "diwali"
        },
        {
            "name": "Laxmi Bomb",
            "sound": "💣 BOOOOOOOOOOMMM! ⚡",
            "effect": "A crisp, deafening blast echoing all across the neighborhood!",
            "category": "bomb"
        },
        {
            "name": "Ground Chakri (Spinning Wheel)",
            "sound": "🌀 WZZZZZZZZZZZZ-ZZZZZZ! 💫",
            "effect": "Spinning furiously on the ground in a mesmerizing circle of purple fire!",
            "category": "diwali"
        },
        {
            "name": "Multi-Color Fountain",
            "sound": "✨ PHUUUUSSSSSSSSHHH-BLAST! 🎇",
            "effect": "Seven colorful bursts illuminated everyone's smiling faces!",
            "category": "fireworks"
        }
    ]

    selected = random.choice(crackers)
    img_url = get_random_image(selected["category"])

    caption = (
        f"🧨 <b>FESTIVE CRACKER EXPLODED!</b> 🧨\n\n"
        f"👤 <b>Lit by:</b> {get_mention(user)}\n"
        f"🎇 <b>Cracker:</b> <b>{selected['name']}</b>\n"
        f"🔊 <b>Sound:</b> <i>{selected['sound']}</i>\n\n"
        f"✨ <i>{selected['effect']}</i>\n\n"
        f"🎆 <b>Happy Diwali to everyone in the chat!</b> 🪔"
    )

    try:
        await update.effective_message.reply_photo(
            photo=img_url,
            caption=caption,
            parse_mode="HTML"
        )
    except Exception:
        await update.effective_message.reply_text(caption, parse_mode="HTML")

async def wish_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /wish command - Send personalized Diwali greeting to someone."""
    user = update.effective_user
    if not user:
        return

    target_id, target_name = await resolve_target_user(update, context)
    if not target_id:
        error_msg = target_name or (
            "💌 <b>How to send a Diwali Wish:</b>\n\n"
            "• Reply to someone's message with <code>/wish</code>\n"
            "• Or type <code>/wish @username</code>\n"
            "• Or type <code>/wish &lt;user_id&gt;</code>"
        )
        await update.effective_message.reply_text(error_msg, parse_mode="HTML")
        return

    if target_id == user.id:
        await update.effective_message.reply_text("Self-love is great, but Diwali is about sharing! Wish someone else in the group! 🪔")
        return

    user_data = await db.get_user(user.id, {"username": user.username, "first_name": user.first_name})
    last_wish = user_data.get("last_wish")

    is_ready, remaining = check_cooldown(last_wish, config.WISH_COOLDOWN_SECONDS)
    if not is_ready:
        time_str = format_remaining_time(remaining)
        await update.effective_message.reply_text(
            f"⏳ Hold on, {get_mention(user)}! You can send another warm wish in <b>{time_str}</b>.",
            parse_mode="HTML"
        )
        return

    target_user = await db.get_user(target_id)
    target_mention = get_mention(target_user, custom_title=target_name)
    sender_mention = get_mention(user)

    wishes_sent = user_data.get("wishes_sent", 0) + 1
    await db.update_user(user.id, {
        "last_wish": datetime.utcnow().isoformat(),
        "wishes_sent": wishes_sent
    })

    greetings = [
        "May Lord Ganesha remove all obstacles from your path and Goddess Lakshmi fill your home with infinite prosperity and good fortune! 🪔✨",
        "Wishing you a year filled with sparkling moments, sweet memories, and endless success! Shubh Deepavali! 🎆",
        "May the light of diyas chase away all darkness, doubts, and worries, guiding you towards bright triumph! 🌟",
        "Sending you tons of happiness, love, laughter, and boxes of sweets on this auspicious festival of lights! 🍬🪔"
    ]
    greeting = random.choice(greetings)
    img_url = get_random_image("wish")

    caption = (
        f"💌 <b>HEARTFELT DIWALI WISH</b> 💌\n\n"
        f"✨ {sender_mention} is sending auspicious festive blessings to {target_mention}!\n\n"
        f"<i>\"{greeting}\"</i>\n\n"
        f"🪔 <b>Happy Diwali to you and your loved ones!</b> ✨\n"
        f"<i>(Wishes shared by {user.first_name}: {wishes_sent})</i>"
    )

    try:
        await update.effective_message.reply_photo(
            photo=img_url,
            caption=caption,
            parse_mode="HTML"
        )
    except Exception:
        await update.effective_message.reply_text(caption, parse_mode="HTML")

async def mithai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mithai command - Share mouth-watering festive sweets with friends."""
    user = update.effective_user
    if not user:
        return

    target_id, target_name = await resolve_target_user(update, context)
    if not target_id:
        error_msg = target_name or (
            "🍬 <b>How to share Mithai:</b>\n\n"
            "• Reply to someone's message with <code>/mithai</code>\n"
            "• Or type <code>/mithai @username</code>\n"
            "• Or type <code>/mithai &lt;user_id&gt;</code>"
        )
        await update.effective_message.reply_text(error_msg, parse_mode="HTML")
        return

    if target_id == user.id:
        await update.effective_message.reply_text("Akele akele saari mithai khaoge? Share with friends! 🍬")
        return

    user_data = await db.get_user(user.id, {"username": user.username, "first_name": user.first_name})
    last_mithai = user_data.get("last_mithai")

    is_ready, remaining = check_cooldown(last_mithai, config.MITHAI_COOLDOWN_SECONDS)
    if not is_ready:
        time_str = format_remaining_time(remaining)
        await update.effective_message.reply_text(
            f"😋 Digestion break! Wait <b>{time_str}</b> before serving more sweets!",
            parse_mode="HTML"
        )
        return

    target_user = await db.get_user(target_id)
    target_mention = get_mention(target_user, custom_title=target_name)
    sender_mention = get_mention(user)

    mithai_sent = user_data.get("mithai_sent", 0) + 1
    await db.update_user(user.id, {
        "last_mithai": datetime.utcnow().isoformat(),
        "mithai_sent": mithai_sent
    })

    sweets = [
        ("Kaju Katli ✨", "silvery, royal diamond cashew fudge that melts on your tongue"),
        ("Motichoor Ladoo 🟡", "fragrant ghee-fried sweet boondi pearls soaked in aromatic cardamom syrup"),
        ("Gulab Jamun 🍯", "piping hot, golden-brown dumplings immersed in rose-scented sugar nectar"),
        ("Rasgulla 🤍", "spongy, juicy cottage cheese dumplings dripping with pure sweetness"),
        ("Crispy Jalebi 🌀", "saffron-infused, swirling orange spirals crunchy and oozing with sweet syrup"),
        ("Besan Ladoo 🌟", "roasted gram flour delight infused with pure desi ghee and roasted almonds")
    ]
    sweet_name, sweet_desc = random.choice(sweets)
    img_url = get_random_image("mithai")

    caption = (
        f"🍬 <b>MITHAI TIME! KUCH MEETHA HO JAYE!</b> 🍬\n\n"
        f"🎁 {sender_mention} lovingly fed delicious <b>{sweet_name}</b> to {target_mention}!\n\n"
        f"<i>\"{sweet_desc}!\"</i>\n\n"
        f"🤤 <i>Munh meetha kijiye aur Diwali ki mithas bantiye!</i>\n"
        f"<i>(Sweets distributed by {user.first_name}: {mithai_sent})</i>"
    )

    try:
        await update.effective_message.reply_photo(
            photo=img_url,
            caption=caption,
            parse_mode="HTML"
        )
    except Exception:
        await update.effective_message.reply_text(caption, parse_mode="HTML")

