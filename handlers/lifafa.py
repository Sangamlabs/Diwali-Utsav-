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

async def lifafa_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /lifafa <total_coins> <slots>
    Allows a user or admin to drop a festive Shagun Red Packet in a group.
    Other members can tap [ 🧧 Open Lifafa ] to receive a random share of the coins!
    """
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message

    if not user or not msg or not chat:
        return

    if chat.type not in ["group", "supergroup"]:
        await msg.reply_text("🧧 Shubh Lifafa can only be sent in group chats! Add me to a group and celebrate with friends!")
        return

    if not context.args or len(context.args) < 2:
        await msg.reply_text(
            "🧧 <b>HOW TO SEND A SHUBH LIFAFA:</b>\n\n"
            "Share festive shagun coins with your group members!\n\n"
            "<b>Usage:</b>\n"
            "<code>/lifafa &lt;total_coins&gt; &lt;number_of_users&gt;</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/lifafa 5000 5</code> — <i>Drops 5,000 coins split randomly among 5 lucky members!</i>\n\n"
            "<i>(Minimum: 500 coins, 2 to 20 slots)</i>",
            parse_mode="HTML"
        )
        return

    try:
        total_coins = int(context.args[0])
        slots = int(context.args[1])
    except ValueError:
        await msg.reply_text("❌ Please enter valid numbers for coins and slots.")
        return

    if total_coins < 500:
        await msg.reply_text("❌ Minimum Lifafa amount is <b>500</b> coins!", parse_mode="HTML")
        return
    if slots < 2 or slots > 25:
        await msg.reply_text("❌ Slots must be between <b>2</b> and <b>25</b> people!", parse_mode="HTML")
        return
    if total_coins / slots < 10:
        await msg.reply_text("❌ Each slot must receive at least 10 coins!")
        return

    # Check sender balance
    user_data = await db.get_user(user.id, {"username": user.username, "first_name": user.first_name})
    if user_data.get("coins", 0) < total_coins:
        await msg.reply_text(
            f"❌ <b>Insufficient Coins!</b>\n\n"
            f"You need <code>{format_number(total_coins)}</code> coins, but you only have <code>{format_number(user_data.get('coins', 0))}</code> coins.",
            parse_mode="HTML"
        )
        return

    # Deduct coins from sender
    await db.deduct_coins(user.id, total_coins)

    lifafa_id = f"lifafa_{uuid.uuid4().hex[:8]}"

    # Distribute random shares that sum exactly to total_coins
    cuts = sorted([random.randint(1, total_coins - 1) for _ in range(slots - 1)])
    cuts = [0] + cuts + [total_coins]
    shares = [cuts[i + 1] - cuts[i] for i in range(slots)]
    random.shuffle(shares)

    # Store lifafa data
    lifafa_data = {
        "lifafa_id": lifafa_id,
        "sender_id": user.id,
        "sender_name": user.first_name,
        "chat_id": chat.id,
        "total_coins": total_coins,
        "slots": slots,
        "shares": shares,
        "claims": [],  # list of {"user_id": int, "name": str, "amount": int}
        "active": True,
        "created_at": datetime.utcnow().isoformat()
    }

    # Save to db setting / drops
    await db.set_setting(lifafa_id, lifafa_data)

    img_url = get_random_image("loot_drop")
    caption = (
        f"🧧 <b>SHUBH DIWALI LIFAFA (SHAGUN PACKET)</b> 🧧\n\n"
        f"🎁 <b>Generous Sender:</b> {get_mention(user)}\n"
        f"🪙 <b>Total Shagun:</b> <code>{format_number(total_coins)}</code> Coins\n"
        f"👥 <b>Slots Available:</b> <b>{slots} Lucky Members</b>\n\n"
        f"<i>Tap below right now to grab your festive shagun!</i>"
    )

    keyboard = [[InlineKeyboardButton(f"🧧 Open Shubh Lifafa (0/{slots})", callback_data=f"open_lifafa:{lifafa_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await msg.reply_photo(photo=img_url, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
    except Exception:
        await msg.reply_text(caption, parse_mode="HTML", reply_markup=reply_markup)

async def lifafa_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle opening of a Shubh Lifafa packet."""
    query = update.callback_query
    if not query or not query.data or not query.data.startswith("open_lifafa:"):
        return

    lifafa_id = query.data.split(":", 1)[1]
    user = query.from_user

    lifafa = await db.get_setting(lifafa_id)
    if not lifafa or not lifafa.get("active", False):
        await query.answer("❌ This Shubh Lifafa has already been fully claimed or expired!", show_alert=True)
        return

    claims = lifafa.get("claims", [])
    # Check if user already claimed
    for c in claims:
        if c["user_id"] == user.id:
            await query.answer(f"⚠️ You already claimed {format_number(c['amount'])} coins from this Lifafa!", show_alert=True)
            return

    # Check remaining shares
    shares = lifafa.get("shares", [])
    if not shares:
        lifafa["active"] = False
        await db.set_setting(lifafa_id, lifafa)
        await query.answer("❌ All slots have been claimed!", show_alert=True)
        return

    amount = shares.pop(0)
    await db.add_coins(user.id, amount)

    claims.append({
        "user_id": user.id,
        "name": user.first_name,
        "amount": amount
    })

    slots = lifafa.get("slots", len(claims))
    is_completed = len(claims) >= slots or len(shares) == 0

    lifafa["claims"] = claims
    lifafa["shares"] = shares
    lifafa["active"] = not is_completed
    await db.set_setting(lifafa_id, lifafa)

    await query.answer(f"🎉 Shagun Unlocked! You received {format_number(amount)} Coins! 🪙", show_alert=True)

    sender_name = lifafa.get("sender_name", "Friend")
    total_coins = lifafa.get("total_coins", 0)

    # Format claims list
    claimed_lines = []
    for idx, c in enumerate(claims):
        clean_name = c["name"].replace("<", "&lt;").replace(">", "&gt;")
        claimed_lines.append(f"{idx+1}. <b>{clean_name}</b>: +<code>{format_number(c['amount'])}</code> 🪙")

    claims_text = "\n".join(claimed_lines)

    if is_completed:
        # Sort to find luckiest king
        sorted_claims = sorted(claims, key=lambda x: x["amount"], reverse=True)
        luckiest = sorted_claims[0]["name"] if sorted_claims else "Someone"

        completed_caption = (
            f"🧧 <b>SHUBH LIFAFA FULLY CLAIMED!</b> 🧧\n\n"
            f"🎁 <b>Sender:</b> <b>{sender_name}</b>\n"
            f"🪙 <b>Total Distributed:</b> <code>{format_number(total_coins)}</code> Coins\n"
            f"👑 <b>Luckiest Player:</b> <b>{luckiest}</b> (+{format_number(sorted_claims[0]['amount'])} 🪙)\n\n"
            f"📜 <b>Winners:</b>\n{claims_text}\n\n"
            f"✨ <i>Send your own with <code>/lifafa &lt;coins&gt; &lt;slots&gt;</code>!</i>"
        )
        try:
            await query.edit_message_caption(caption=completed_caption, parse_mode="HTML", reply_markup=None)
        except Exception:
            pass
    else:
        # Still has remaining slots
        in_progress_caption = (
            f"🧧 <b>SHUBH DIWALI LIFAFA ({len(claims)}/{slots} CLAIMED)</b> 🧧\n\n"
            f"🎁 <b>Sender:</b> <b>{sender_name}</b>\n"
            f"🪙 <b>Total Shagun:</b> <code>{format_number(total_coins)}</code> Coins\n\n"
            f"📜 <b>Claimed so far:</b>\n{claims_text}\n\n"
            f"⚡ <i>{slots - len(claims)} slot(s) remaining! Tap below!</i>"
        )
        keyboard = [[InlineKeyboardButton(f"🧧 Open Shubh Lifafa ({len(claims)}/{slots})", callback_data=f"open_lifafa:{lifafa_id}")]]
        try:
            await query.edit_message_caption(caption=in_progress_caption, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            pass

