import random
import uuid
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import config
from database import db
from utils import (
    get_mention,
    format_number,
    get_random_image
)

async def group_message_tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Tracks group activity.
    When a group reaches minimum message threshold (default 5 messages),
    triggers random festive spawns (Interactive Loot Drop or Festive Cracker Burst).
    """
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not message or not chat or not user or user.is_bot:
        return

    # Only process group chats
    if chat.type not in ["group", "supergroup"]:
        return

    # Register user in DB
    await db.get_user(user.id, {"username": user.username, "first_name": user.first_name})

    # Increment message count for this group
    group = await db.get_group(chat.id, chat.title)
    if not group.get("drops_enabled", True):
        return

    min_messages = group.get("min_messages", config.DEFAULT_MIN_GROUP_MESSAGES)
    current_count = await db.increment_group_messages(chat.id)

    if current_count >= min_messages:
        # Reset counter
        await db.reset_group_messages(chat.id)

        # 50% chance of interactive drop, 50% chance of festive visual burst
        if random.random() < config.RANDOM_DROP_CHANCE:
            await spawn_interactive_drop(chat.id, context)
        else:
            await spawn_festive_burst(chat.id, context)

async def spawn_interactive_drop(
    chat_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    custom_coins: int = 0,
    custom_msg: str = "",
    custom_img: str = "",
    custom_btn: str = "",
    max_claims: int = 1
):
    """Spawn an interactive claimable drop in a group."""
    drop_id = f"drop_{uuid.uuid4().hex[:8]}"
    coins = custom_coins or random.randint(1000, 3000)
    img_url = custom_img or get_random_image("loot_drop")
    btn_text = custom_btn or f"🎁 Claim {format_number(coins)} Coins!"

    caption = custom_msg or (
        f"🎁 <b>FESTIVE SURPRISE DROP!</b> 🎁\n\n"
        f"✨ A sparkling festive treasure bag has appeared in the chat!\n"
        f"🪙 <b>Prize:</b> <code>{format_number(coins)}</code> Coins\n"
        f"⚡ <b>Slots:</b> Fastest {max_claims} player{'s' if max_claims > 1 else ''} to tap wins!\n\n"
        f"<i>Tap the button below right now to claim!</i>"
    )

    drop_data = {
        "drop_id": drop_id,
        "chat_id": chat_id,
        "reward_type": "coins",
        "reward_value": coins,
        "max_claims": max_claims,
        "claimed_by": [],
        "active": True,
        "created_at": datetime.utcnow().isoformat()
    }
    await db.create_drop(drop_id, drop_data)

    keyboard = [[InlineKeyboardButton(btn_text, callback_data=f"claim_drop:{drop_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=img_url,
            caption=caption,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"Failed to spawn drop in chat {chat_id}: {e}")

async def spawn_festive_burst(chat_id: int, context: ContextTypes.DEFAULT_TYPE, event_type: str = ""):
    """Spawn a random aesthetic festive burst (Diya, Cracker, Bomb, Fireworks)."""
    events = ["diya", "fireworks", "bomb", "cracker"]
    chosen = event_type if event_type in events else random.choice(events)

    if chosen == "diya":
        img_url = get_random_image("diya")
        caption = (
            "🪔 <b>SACRED DIYA SHINES BRIGHT!</b> 🪔\n\n"
            "✨ <i>A divine clay lamp flickers with pure warmth in the group, dispelling all negativity!</i>\n"
            "🌟 <b>May Lord Rama bring peace, unity, and bliss to everyone here!</b>"
        )
    elif chosen == "bomb":
        img_url = get_random_image("bomb")
        caption = (
            "💣 <b>DHAAAMAKKAAA! SUTLI BOMB DETONATED!</b> 💥\n\n"
            "🔊 <i>*BOOOOOOOOMMMMMMMMMMM!*</i> 🔊\n"
            "💨 The whole chat vibrates as festive smoke fills the air!\n"
            "🧨 <b>Happy Diwali to all members!</b>"
        )
    elif chosen == "fireworks":
        img_url = get_random_image("fireworks")
        caption = (
            "🎆 <b>SKY BURSTS INTO SPECTACULAR COLORS!</b> 🎆\n\n"
            "🚀 <i>Whistling rockets zoom into the starry night, painting the sky with sparkling golden and emerald palms!</i>\n"
            "✨ <b>Enjoy the festival of lights!</b> 🪔"
        )
    else:
        img_url = get_random_image("diwali")
        caption = (
            "🎇 <b>SPARKLING DIWALI CELEBRATION!</b> 🎇\n\n"
            "✨ <i>Golden sparklers and swirling chakris light up the festive ground!</i>\n"
            "🍬 <i>Don't forget to share sweets with each other using /mithai and /gift!</i>"
        )

    try:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=img_url,
            caption=caption,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Failed to spawn festive burst in chat {chat_id}: {e}")

async def claim_drop_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle claiming of interactive loot drops."""
    query = update.callback_query
    if not query or not query.data:
        return

    data = query.data
    if not data.startswith("claim_drop:"):
        return

    drop_id = data.split(":", 1)[1]
    user = query.from_user

    drop = await db.get_drop(drop_id)
    if not drop or not drop.get("active", False):
        await query.answer("❌ This drop has already expired or been fully claimed!", show_alert=True)
        return

    claimed_by = drop.get("claimed_by", [])
    if user.id in claimed_by:
        await query.answer("⚠️ You have already claimed this drop!", show_alert=True)
        return

    success, msg = await db.claim_drop(drop_id, user.id)
    if not success:
        await query.answer(f"❌ {msg}", show_alert=True)
        return

    # Grant reward
    reward_type = drop.get("reward_type", "coins")
    reward_value = drop.get("reward_value", 1000)

    if reward_type == "coins":
        new_balance = await db.add_coins(user.id, reward_value)
        await query.answer(f"🎉 Winner! You received {format_number(reward_value)} Coins!", show_alert=True)
    else:
        # Gift reward
        await db.add_gift_to_inventory(user.id, str(reward_value))
        await query.answer(f"🎉 Winner! You received a festive gift!", show_alert=True)

    # Check if all slots claimed
    updated_drop = await db.get_drop(drop_id)
    new_claimed_by = updated_drop.get("claimed_by", [])
    max_claims = updated_drop.get("max_claims", 1)

    winner_mentions = []
    for uid in new_claimed_by:
        u_doc = await db.get_user(uid)
        winner_mentions.append(get_mention(u_doc))

    winners_str = ", ".join(winner_mentions)

    if len(new_claimed_by) >= max_claims:
        # Fully claimed: Edit message
        edit_caption = (
            f"🏆 <b>FESTIVE DROP CLAIMED!</b> 🏆\n\n"
            f"⚡ <b>Fastest Fingers:</b> {winners_str}\n"
            f"🪙 <b>Prize Won:</b> <code>{format_number(reward_value)}</code> Coins each!\n\n"
            f"<i>Keep chatting in the group to trigger the next festive drop!</i> 🪔"
        )
        try:
            await query.edit_message_caption(
                caption=edit_caption,
                parse_mode="HTML",
                reply_markup=None
            )
        except Exception:
            pass
    else:
        # Partially claimed: update remaining slots
        remaining_slots = max_claims - len(new_claimed_by)
        edit_caption = (
            f"🎁 <b>FESTIVE DROP IN PROGRESS!</b> 🎁\n\n"
            f"🪙 <b>Prize:</b> <code>{format_number(reward_value)}</code> Coins\n"
            f"👤 <b>Claimed so far:</b> {winners_str}\n"
            f"⚡ <b>Remaining Slots:</b> {remaining_slots}\n\n"
            f"<i>Tap below to claim!</i>"
        )
        try:
            await query.edit_message_caption(
                caption=edit_caption,
                parse_mode="HTML",
                reply_markup=query.message.reply_markup
            )
        except Exception:
            pass

