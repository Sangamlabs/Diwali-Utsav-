from datetime import datetime
from typing import Optional
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import config
from database import db
from utils import (
    get_mention,
    format_number,
    resolve_target_user
)

async def gift_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /gift or /shop command."""
    user = update.effective_user
    if not user:
        return

    # Check if target is provided via reply or argument
    target_id, target_name = await resolve_target_user(update, context)

    if not target_id:
        # User invoked /gift or /shop standalone: Show interactive Bazaar
        user_data = await db.get_user(user.id)
        coins = user_data.get("coins", 0)

        shop_text = (
            "🛍️ <b>SHUBH DIWALI FESTIVE BAZAAR</b> 🛍️\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🪙 <b>Your Balance:</b> <code>{format_number(coins)}</code> Coins\n\n"
            "Surprise your friends in group chats with sweets, crackers & gold coins!\n\n"
            "💡 <b>How to deliver a gift:</b>\n"
            "• <b>Reply</b> to a friend's message with <code>/gift</code>\n"
            "• Or type <code>/gift @username</code>\n"
            "• Or type <code>/gift &lt;user_id&gt;</code>\n\n"
            "<i>Tap any item below to view its festive details:</i>"
        )

        buttons = []
        row = []
        for g_id, g in config.GIFTS.items():
            row.append(InlineKeyboardButton(f"{g['emoji']} {g['name']}", callback_data=f"gift_inspect:{g_id}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        buttons.append([
            InlineKeyboardButton("🎁 My Gift Box", callback_data="view_my_gifts"),
            InlineKeyboardButton("🎒 My Profile", callback_data="view_profile_quick")
        ])
        buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="nav_home")])

        reply_markup = InlineKeyboardMarkup(buttons)
        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(shop_text, parse_mode="HTML", reply_markup=reply_markup)
            except Exception:
                await update.callback_query.message.reply_text(shop_text, parse_mode="HTML", reply_markup=reply_markup)
        else:
            await update.effective_message.reply_text(shop_text, parse_mode="HTML", reply_markup=reply_markup)
        return

    if target_id == user.id:
        await update.effective_message.reply_text("Self-love is great, but Diwali is about gifting others! Share the joy with a friend! 🎁")
        return

    target_user = await db.get_user(target_id)
    target_mention = get_mention(target_user, custom_title=target_name)
    sender_data = await db.get_user(user.id, {"username": user.username, "first_name": user.first_name})
    sender_coins = sender_data.get("coins", 0)

    text = (
        f"🎁 <b>SELECT A DIWALI GIFT FOR {target_mention}</b> 🎁\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🪙 <b>Your Coin Balance:</b> <code>{format_number(sender_coins)}</code> Coins\n\n"
        f"<i>Select a festive item to purchase and deliver immediately:</i>"
    )

    buttons = []
    row = []
    for g_id, g in config.GIFTS.items():
        btn_text = f"{g['emoji']} {g['name']} ({format_number(g['price'])} 🪙)"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"gift_send:{g_id}:{target_id}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")])

    await update.effective_message.reply_text(
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def gift_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle gift interactions & inspection."""
    query = update.callback_query
    if not query or not query.data:
        return

    data = query.data
    user = query.from_user

    if data.startswith("gift_inspect:"):
        await query.answer()
        gift_id = data.split(":", 1)[1]
        g = config.GIFTS.get(gift_id)
        if not g:
            return

        user_data = await db.get_user(user.id)
        coins = user_data.get("coins", 0)
        can_afford = "✅ You can afford this!" if coins >= g["price"] else f"❌ Need {format_number(g['price'] - coins)} more coins"

        inspect_text = (
            f"{g['emoji']} <b>{g['name'].upper()}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📜 <b>Description:</b>\n<i>\"{g['description']}\"</i>\n\n"
            f"🪙 <b>Price:</b> <code>{format_number(g['price'])}</code> Coins\n"
            f"💳 <b>Your Status:</b> {can_afford}\n\n"
            f"💡 <i>To deliver this gift, reply to your friend's message with <code>/gift</code>!</i>"
        )
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Bazaar", callback_data="shop_view")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="nav_home")]
        ]
        try:
            await query.edit_message_text(inspect_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            await query.message.reply_text(inspect_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("gift_send:"):
        parts = data.split(":")
        if len(parts) != 3:
            return
        gift_id = parts[1]
        try:
            target_id = int(parts[2])
        except ValueError:
            return

        gift_info = config.GIFTS.get(gift_id)
        if not gift_info:
            await query.answer("Gift not found!", show_alert=True)
            return

        price = gift_info["price"]
        sender_data = await db.get_user(user.id, {"username": user.username, "first_name": user.first_name})
        sender_coins = sender_data.get("coins", 0)

        # Check balance
        if sender_coins < price:
            needed = price - sender_coins
            await query.answer(
                f"❌ Insufficient Coins!\n\nYou have {format_number(sender_coins)} coins.\nYou need {format_number(needed)} more coins.\nUse /daily or /loot to collect coins!",
                show_alert=True
            )
            return

        # Deduct coins
        success = await db.deduct_coins(user.id, price)
        if not success:
            await query.answer("Transaction failed. Please try again.", show_alert=True)
            return

        sender_info = {
            "sender_id": user.id,
            "sender_name": user.first_name or "Friend",
            "sender_username": user.username or "",
            "gift_id": gift_id,
            "gift_name": gift_info["name"],
            "gift_emoji": gift_info["emoji"],
            "price": price,
            "received_at": datetime.utcnow().isoformat()
        }

        # Add to recipient inventory and log sender
        await db.add_gift_to_inventory(target_id, gift_id, sender_info)

        # Update sender stats
        gifts_sent = sender_data.get("gifts_sent", 0) + 1
        await db.update_user(user.id, {"gifts_sent": gifts_sent})

        target_user = await db.get_user(target_id)
        sender_mention = get_mention(user)
        target_mention = get_mention(target_user)

        caption = (
            f"🎉 <b>FESTIVE GIFT DELIVERED!</b> 🎉\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎁 {sender_mention} gifted <b>{gift_info['name']}</b> {gift_info['emoji']} to {target_mention}!\n\n"
            f"<i>\"{gift_info['description']}\"</i>\n\n"
            f"🪙 <b>Gift Value:</b> <code>{format_number(price)}</code> Coins\n"
            f"📦 <b>Check Your Gifts:</b> Type <code>/mygifts</code> to view all received gifts & senders!\n\n"
            f"🪔 <i>May this Diwali bring boundless sweetness and joy!</i>"
        )

        try:
            await query.message.delete()
        except Exception:
            pass

        try:
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=gift_info["image"],
                caption=caption,
                parse_mode="HTML"
            )
        except Exception:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=caption,
                parse_mode="HTML"
            )

    elif data == "shop_view":
        await query.answer()
        user_data = await db.get_user(user.id)
        coins = user_data.get("coins", 0)

        shop_text = (
            "🛍️ <b>SHUBH DIWALI FESTIVE BAZAAR</b> 🛍️\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🪙 <b>Your Balance:</b> <code>{format_number(coins)}</code> Coins\n\n"
            "Surprise your friends in group chats with sweets, crackers & gold coins!\n\n"
            "💡 <b>How to deliver a gift:</b>\n"
            "• <b>Reply</b> to a friend's message with <code>/gift</code>\n"
            "• Or type <code>/gift @username</code>\n\n"
            "<i>Tap any item below to inspect it:</i>"
        )

        buttons = []
        row = []
        for g_id, g in config.GIFTS.items():
            row.append(InlineKeyboardButton(f"{g['emoji']} {g['name']}", callback_data=f"gift_inspect:{g_id}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        buttons.append([
            InlineKeyboardButton("🎁 My Gift Box", callback_data="view_my_gifts"),
            InlineKeyboardButton("🎒 My Profile", callback_data="view_profile_quick")
        ])
        buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="nav_home")])

        try:
            await query.edit_message_text(shop_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons))
        except Exception:
            await query.message.reply_text(shop_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "cancel_action":
        try:
            await query.message.delete()
        except Exception:
            await query.edit_message_text("❌ Action cancelled.")

# --- My Received Gifts Directory & Dossier ---

def format_time_ago(iso_str: Optional[str]) -> str:
    """Format ISO timestamp into friendly relative time e.g. '5m ago' or '2h ago'."""
    if not iso_str:
        return "recently"
    try:
        dt = datetime.fromisoformat(iso_str)
        seconds = int((datetime.utcnow() - dt).total_seconds())
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        elif seconds < 86400:
            return f"{seconds // 3600}h ago"
        elif seconds < 604800:
            return f"{seconds // 86400}d ago"
        else:
            return dt.strftime("%d %b %Y")
    except Exception:
        return "recently"

async def generate_my_gifts_view(user_id: int) -> tuple[str, InlineKeyboardMarkup]:
    """Generate rich received gifts box showing items and who gifted them."""
    u_doc = await db.get_user(user_id)
    first_name = (u_doc.get("first_name") or "Friend").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    total_received = u_doc.get("gifts_received", 0)
    inventory = u_doc.get("inventory", {})
    history = u_doc.get("received_gifts", [])

    lines = [
        f"🎁 <b>{first_name.upper()}'S DIWALI GIFT BOX</b> 🎁",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📦 <b>Total Gifts Received:</b> <code>{total_received}</code>\n"
    ]

    # Inventory collection breakdown
    inv_items = []
    for g_id, g in config.GIFTS.items():
        cnt = inventory.get(g_id, 0)
        if cnt > 0:
            inv_items.append(f"• {g['emoji']} <b>{g['name']}</b>: <code>×{cnt}</code>")

    if inv_items:
        lines.append("🎒 <b>COLLECTION SUMMARY:</b>")
        lines.extend(inv_items)
        lines.append("")
    else:
        lines.append("🎒 <b>COLLECTION:</b> <i>No gifts in inventory yet!</i>\n")

    # History of who sent them
    lines.append("💌 <b>WHO SENT YOU GIFTS (Sender History):</b>")
    if history:
        for idx, item in enumerate(history[:12], start=1):
            g_name = item.get("gift_name", "Festive Gift")
            g_emoji = item.get("gift_emoji", "🎁")
            s_name = (item.get("sender_name") or "A Friend").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            s_id = item.get("sender_id", 0)
            s_uname = f"(@{item.get('sender_username')})" if item.get("sender_username") else ""
            time_ago = format_time_ago(item.get("received_at"))

            s_mention = f'<a href="tg://user?id={s_id}">{s_name}</a>' if s_id else s_name
            lines.append(
                f"<b>{idx}. {g_emoji} {g_name}</b>\n"
                f"   ├ 👤 From: {s_mention} {s_uname}\n"
                f"   └ 🕒 Received: <i>{time_ago}</i>"
            )
        if len(history) > 12:
            lines.append(f"\n<i>...and {len(history) - 12} more earlier gift(s)</i>")
    elif total_received > 0 or inv_items:
        lines.append("<i>You have gifts in your inventory! (Detailed sender names will be recorded for all future gifts you receive).</i>")
    else:
        lines.append(
            "<i>Your gift box is currently empty!\n"
            "Ask friends in groups to surprise you with <code>/gift</code>! 🪔</i>"
        )

    lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("<i>💡 Want to surprise someone? Reply to their message with <code>/gift</code>!</i>")

    keyboard = [
        [
            InlineKeyboardButton("🛍️ Gift Bazaar (/shop)", callback_data="shop_view"),
            InlineKeyboardButton("🎒 Full Profile", callback_data="view_profile_quick")
        ],
        [
            InlineKeyboardButton("🔄 Refresh Gift Box", callback_data="view_my_gifts"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="nav_home")
        ]
    ]

    return "\n".join(lines), InlineKeyboardMarkup(keyboard)

async def my_gifts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /mygifts, /receivedgifts, /giftbox, /giftsreceived, /giftslist
    Allows user to list all the gifts they got and see who sent each gift.
    """
    user = update.effective_user
    msg = update.effective_message
    if not user or not msg:
        return

    # Check if target specified (reply, @username, id)
    target_id, target_name = await resolve_target_user(update, context)
    inspect_id = target_id if target_id else user.id

    text, markup = await generate_my_gifts_view(inspect_id)
    await msg.reply_text(text, parse_mode="HTML", reply_markup=markup, disable_web_page_preview=True)

