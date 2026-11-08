from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import config
from database import db
from utils import (
    get_mention,
    format_number,
    get_random_image,
    check_cooldown,
    format_remaining_time,
    format_banner,
    format_divider,
    to_font,
    resolve_target_user
)

def get_rank_details(coins: int) -> tuple[str, str, int]:
    """
    Returns (rank_title, progress_bar, next_target)
    """
    ranks = [
        ("🕯️ Diwali Newbie", 5000),
        ("🍬 Festive Enthusiast", 20000),
        ("🪔 Sacred Diya Master", 50000),
        ("🎆 Firecracker King", 100000),
        ("👑 Royal Shagun Maharaja", 200000),
        ("🌟 Param Dhan Kuber", 999999999)
    ]
    prev_limit = 0
    for title, limit in ranks:
        if coins < limit:
            span = limit - prev_limit
            progress = max(0, coins - prev_limit)
            percent = min(100, int((progress / span) * 100))
            filled = int(percent / 10)
            bar = "█" * filled + "░" * (10 - filled)
            return title, f"<code>[{bar}]</code> {percent}%", limit
        prev_limit = limit

    return "🌟 Param Dhan Kuber (MAX)", "<code>[██████████]</code> 100%", coins

async def daily_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /daily command - 5,000 coins once every 24 hours."""
    user = update.effective_user
    if not user:
        return

    user_data = await db.get_user(user.id, {"username": user.username, "first_name": user.first_name})
    last_daily = user_data.get("last_daily")

    daily_cooldown_sec = config.DAILY_COOLDOWN_HOURS * 3600
    is_ready, remaining = check_cooldown(last_daily, daily_cooldown_sec)

    if not is_ready:
        time_str = format_remaining_time(remaining)
        await update.effective_message.reply_text(
            f"⏳ <b>DAILY BONUS COOLDOWN</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Dear {get_mention(user)}, you have already collected today's sacred shagun!\n\n"
            f"🕒 <b>Next Blessing In:</b> <code>{time_str}</code> 🪔\n"
            f"<i>Come back tomorrow for your next 5,000 coins!</i>",
            parse_mode="HTML"
        )
        return

    daily_reward = await db.get_setting("daily_coins", config.DAILY_COINS)
    new_balance = await db.add_coins(user.id, daily_reward)
    await db.update_user(user.id, {"last_daily": datetime.utcnow().isoformat()})

    img_url = config.IMAGE_URLS.get("daily", get_random_image("welcome"))
    caption = (
        f"🎉 <b>DAILY DIWALI SHAGUN CLAIMED!</b> 🎉\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Goddess Lakshmi showers her golden blessing upon {get_mention(user)}!\n\n"
        f"🪙 <b>Claimed:</b> +<code>{format_number(daily_reward)}</code> Coins\n"
        f"💰 <b>Total Balance:</b> <code>{format_number(new_balance)}</code> Coins\n\n"
        f"<i>Spend your wealth in the /shop or multiply it in /games!</i>"
    )

    keyboard = [
        [
            InlineKeyboardButton("🎮 Play Games", callback_data="help_games"),
            InlineKeyboardButton("🎁 Gift Shop", callback_data="shop_view")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await update.effective_message.reply_photo(photo=img_url, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
    except Exception:
        await update.effective_message.reply_text(caption, parse_mode="HTML", reply_markup=reply_markup)

async def loot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /loot command - 10,000 coins with dynamic admin-adjustable cooldown (default 6h)."""
    user = update.effective_user
    if not user:
        return

    user_data = await db.get_user(user.id, {"username": user.username, "first_name": user.first_name})
    last_loot = user_data.get("last_loot")

    loot_hours = await db.get_setting("loot_cooldown_hours", config.DEFAULT_LOOT_COOLDOWN_HOURS)
    loot_cooldown_sec = int(loot_hours * 3600)

    is_ready, remaining = check_cooldown(last_loot, loot_cooldown_sec)

    if not is_ready:
        time_str = format_remaining_time(remaining)
        await update.effective_message.reply_text(
            f"🛡️ <b>FESTIVE VAULT IS CURRENTLY LOCKED</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Hey {get_mention(user)}, the royal treasure vault is recharging!\n\n"
            f"🕒 <b>Vault Unlocks In:</b> <code>{time_str}</code> 💰\n"
            f"<i>Cooldown duration: {loot_hours} hours.</i>",
            parse_mode="HTML"
        )
        return

    loot_reward = await db.get_setting("loot_coins", config.DEFAULT_LOOT_COINS)
    new_balance = await db.add_coins(user.id, loot_reward)
    await db.update_user(user.id, {"last_loot": datetime.utcnow().isoformat()})

    img_url = config.IMAGE_URLS.get("loot", get_random_image("loot_drop"))
    caption = (
        f"💎 <b>MASSIVE DIWALI VAULT LOOTED!</b> 💎\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Jackpot! {get_mention(user)} breached the festive treasure vault!\n\n"
        f"🪙 <b>Loot Collected:</b> +<code>{format_number(loot_reward)}</code> Coins\n"
        f"💰 <b>Total Balance:</b> <code>{format_number(new_balance)}</code> Coins\n\n"
        f"<i>Vault recharges in {loot_hours} hours. Use /profile to see your status!</i>"
    )

    keyboard = [
        [
            InlineKeyboardButton("🎒 My Profile", callback_data="view_profile_quick"),
            InlineKeyboardButton("🎁 Gift Shop", callback_data="shop_view")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await update.effective_message.reply_photo(photo=img_url, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
    except Exception:
        await update.effective_message.reply_text(caption, parse_mode="HTML", reply_markup=reply_markup)

async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /profile or /balance command with elevated UX."""
    user = update.effective_user
    if not user:
        return

    user_data = await db.get_user(user.id, {"username": user.username, "first_name": user.first_name})
    coins = user_data.get("coins", 0)
    rank_title, progress_bar, next_target = get_rank_details(coins)

    inventory = user_data.get("inventory", {})
    inv_lines = []
    if inventory:
        for gift_id, count in inventory.items():
            gift_info = config.GIFTS.get(gift_id, {})
            name = gift_info.get("name", gift_id.title())
            emoji = gift_info.get("emoji", "🎁")
            inv_lines.append(f"  • {emoji} <b>{name}</b> × <code>{count}</code>")
    else:
        inv_lines.append("  <i>No gifts yet! Ask friends in groups to /gift you!</i>")

    # Badges calculation
    badges = []
    if user_data.get("last_diya"):
        badges.append("🪔 Diya Illuminator")
    if user_data.get("gifts_sent", 0) > 0:
        badges.append("🎁 Master Gifter")
    if user_data.get("wishes_sent", 0) > 0:
        badges.append("💌 Warm Wisher")
    if user_data.get("mithai_sent", 0) > 0:
        badges.append("🍬 Sweet Feeder")
    if coins >= 50000:
        badges.append("👑 Wealth Lord")
    if not badges:
        badges.append("🕯️ Diwali Traveler")

    user_theme = user_data.get("theme", "royal")
    banner = format_banner("Festive Passport", user_theme)
    divider = format_divider(user_theme)

    profile_text = (
        f"{banner}\n"
        f"👤 <b>Player:</b> {get_mention(user)}\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
        f"🎖️ <b>Rank:</b> <b>{rank_title}</b>\n"
        f"📈 <b>Progress to Next Rank:</b>\n"
        f"{progress_bar} <i>(Next: {format_number(next_target)} 🪙)</i>\n\n"
        f"🪙 <b>Shagun Coins:</b> <code>{format_number(coins)}</code> 🪙\n"
        f"{divider}\n"
        f"🎒 <b>Received Gift Collection:</b>\n"
        + "\n".join(inv_lines) + "\n\n"
        f"🏅 <b>Earned Badges:</b>\n"
        f"• " + " • ".join(badges) + "\n\n"
        f"📊 <b>Celebration Activity:</b>\n"
        f"• 💌 Wishes: <code>{user_data.get('wishes_sent', 0)}</code> | 🍬 Sweets: <code>{user_data.get('mithai_sent', 0)}</code>\n"
        f"• 🎁 Gifts Sent: <code>{user_data.get('gifts_sent', 0)}</code> | 📦 Received: <code>{user_data.get('gifts_received', 0)}</code>"
    )

    keyboard = [
        [
            InlineKeyboardButton("🎁 My Gifts Box", callback_data="view_my_gifts"),
            InlineKeyboardButton("🛍️ Gift Bazaar", callback_data="shop_view")
        ],
        [
            InlineKeyboardButton("🎮 Games Hub", callback_data="help_games"),
            InlineKeyboardButton("🏆 Leaderboard", callback_data="lb_coins")
        ],
        [
            InlineKeyboardButton("🎨 UI Theme & Fonts", callback_data="theme_menu"),
            InlineKeyboardButton("🏠 Home", callback_data="nav_home")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(profile_text, parse_mode="HTML", reply_markup=reply_markup)
        except Exception:
            await update.callback_query.message.reply_text(profile_text, parse_mode="HTML", reply_markup=reply_markup)
    else:
        await update.effective_message.reply_text(profile_text, parse_mode="HTML", reply_markup=reply_markup)

async def leaderboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /top or /leaderboard command."""
    await render_leaderboard(update, context, sort_by="coins")

async def render_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE, sort_by: str = "coins"):
    """Render sleek leaderboard view."""
    top_users = await db.get_top_users(sort_by=sort_by, limit=10)

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    titles = {
        "coins": "🪙 <b>RICHEST DIWALI PLAYERS</b>",
        "gifts_sent": "🎁 <b>MOST GENEROUS GIFTERS</b>",
        "wishes_sent": "💌 <b>TOP DIWALI WISHERS</b>"
    }

    lines = [
        f"{titles.get(sort_by, '🏆 LEADERBOARDS')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ]

    if not top_users:
        lines.append("<i>No records found yet! Be the first to claim your spot!</i>")
    else:
        for idx, u in enumerate(top_users):
            medal = medals[idx] if idx < len(medals) else f"#{idx+1}"
            name = (u.get("first_name") or "Player")[:14]
            clean_name = name.replace("<", "&lt;").replace(">", "&gt;")
            val = u.get(sort_by, 0)
            if sort_by == "coins":
                val_str = f"{format_number(val)} 🪙"
            else:
                val_str = f"{val} sent"
            lines.append(f"{medal} <b>{clean_name}</b> — <code>{val_str}</code>")

    lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("<i>Switch ranking category:</i>")
    text = "\n".join(lines)

    keyboard = [
        [
            InlineKeyboardButton("🪙 Richest", callback_data="lb_coins"),
            InlineKeyboardButton("🎁 Top Gifters", callback_data="lb_gifts_sent"),
            InlineKeyboardButton("💌 Top Wishers", callback_data="lb_wishes_sent")
        ],
        [
            InlineKeyboardButton("🎒 My Profile", callback_data="view_profile_quick"),
            InlineKeyboardButton("🏠 Home", callback_data="nav_home")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text=text, parse_mode="HTML", reply_markup=reply_markup)
        except Exception:
            pass
    else:
        await update.effective_message.reply_text(text=text, parse_mode="HTML", reply_markup=reply_markup)

# --- Normal User Peer-to-Peer Coin Transfer (/pay) ---

async def pay_coins_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /pay, /transfer, /sendcoins, or /givecoins for regular users.
    Transfers coins from the sender's personal balance to another user.
    """
    user = update.effective_user
    msg = update.effective_message
    if not user or not msg:
        return

    # Check target
    target_id, target_name = await resolve_target_user(update, context)

    amount = None
    if len(context.args) >= 2:
        if context.args[1].isdigit():
            amount = int(context.args[1])
        elif context.args[0].isdigit():
            amount = int(context.args[0])
    elif len(context.args) == 1 and msg.reply_to_message:
        if context.args[0].isdigit():
            amount = int(context.args[0])

    if not target_id or not amount:
        await msg.reply_text(
            "🪙 <b>HOW TO TRANSFER COINS TO A FRIEND:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Share your festive coins as shagun with other members!\n\n"
            "<b>Usage:</b>\n"
            "• <b>Reply</b> to a user's message: <code>/pay &lt;amount&gt;</code>\n"
            "• Or type: <code>/pay @username &lt;amount&gt;</code>\n"
            "• Or type: <code>/pay &lt;user_id&gt; &lt;amount&gt;</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/pay 500</code> <i>(replying to someone)</i>\n"
            "<code>/pay @username 1000</code>\n\n"
            "<i>(Minimum transfer: 50 coins)</i>",
            parse_mode="HTML"
        )
        return

    if target_id == user.id:
        await msg.reply_text("❌ You cannot transfer coins to yourself!")
        return

    if amount < 50:
        await msg.reply_text("❌ Minimum transfer amount is <b>50</b> coins!", parse_mode="HTML")
        return

    sender_data = await db.get_user(user.id, {"username": user.username, "first_name": user.first_name})
    sender_coins = sender_data.get("coins", 0)

    if sender_coins < amount:
        await msg.reply_text(
            f"❌ <b>Insufficient Coins!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"You want to send <code>{format_number(amount)}</code> coins, but you only have <code>{format_number(sender_coins)}</code> coins.\n"
            f"Earn more with /daily, /loot, /diya, or /games!",
            parse_mode="HTML"
        )
        return

    # Deduct from sender
    await db.deduct_coins(user.id, amount)
    # Add to receiver
    await db.add_coins(target_id, amount)

    sender_new_bal = sender_coins - amount
    target_user = await db.get_user(target_id)
    sender_mention = get_mention(user)
    target_mention = get_mention(target_user, custom_title=target_name)

    receipt_text = (
        f"💸 <b>FESTIVE SHAGUN TRANSFER SUCCESSFUL!</b> 🪙\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Sender:</b> {sender_mention}\n"
        f"🎯 <b>Recipient:</b> {target_mention}\n"
        f"🪙 <b>Transferred:</b> <code>{format_number(amount)}</code> Coins\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 <b>Your Remaining Balance:</b> <code>{format_number(sender_new_bal)}</code> Coins\n\n"
        f"✨ <i>Shubh Deepavali! May your festive generosity bring boundless abundance!</i> 🪔"
    )

    await msg.reply_text(receipt_text, parse_mode="HTML")
