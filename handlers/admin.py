import asyncio
import platform
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import config
from database import db
from utils import (
    is_owner,
    is_admin,
    add_dynamic_admin,
    remove_dynamic_admin,
    get_all_admins,
    get_mention,
    format_number,
    resolve_target_user,
    check_cooldown,
    format_remaining_time,
    VALID_IMAGE_CATEGORIES,
    get_category_images,
    add_custom_image,
    remove_custom_image,
    reset_custom_images
)
from handlers.group_activity import spawn_interactive_drop, spawn_festive_burst

BOT_START_TIME = datetime.utcnow()

async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin or /adminhelp command."""
    user = update.effective_user
    if not user or not is_admin(user.id):
        await update.effective_message.reply_text("⛔ Access Denied: You are not authorized as an administrator.")
        return

    admin_text = (
        "👑 <b>DIWALI BOT - ADMIN CONTROL PANEL</b> 👑\n\n"
        "🛡️ <b>Admin Role Controls (Owner Only):</b>\n"
        "• <code>/addadmin &lt;user_id or reply&gt;</code> — Promote user to Admin\n"
        "• <code>/deladmin &lt;user_id or reply&gt;</code> — Demote an Admin\n"
        "• <code>/admins</code> — List all current Owners and Admins\n\n"
        "🖼️ <b>Custom Command & Spawn Images:</b>\n"
        "• <code>/categories</code> — Check all available categories with active image counts\n"
        "• <code>/addimage &lt;category&gt; &lt;url&gt;</code> — Add image URL for a command/spawn\n"
        "• <i>(Or reply to any photo with <code>/addimage &lt;category&gt;</code>)</i>\n"
        "• <code>/listimages [category]</code> — View active images for commands\n"
        "• <code>/delimage &lt;category&gt; &lt;index&gt;</code> — Delete an image from category\n"
        "• <code>/resetimages [category]</code> — Reset back to config defaults\n"
        "  <i>Valid Categories: diya, diwali, wish, mithai, bomb, fireworks, loot_drop, welcome, daily, loot</i>\n\n"
        "⚡ <b>Force Drop & Spawn Controls:</b>\n"
        "• <code>/fdrop &lt;coins&gt; [max_claims]</code> — Spawn coin drop in this group\n"
        "• <code>/fdropall &lt;coins&gt; [max_claims]</code> — Spawn coin drop in ALL registered groups\n"
        "• <code>/fdrop_custom &lt;coins&gt; | &lt;slots&gt; | &lt;button_text&gt; | &lt;image_url&gt; | &lt;message&gt;</code> — Full custom drop\n"
        "• <code>/fspawn [diya|bomb|fireworks|cracker]</code> — Force spawn aesthetic festive message here\n"
        "• <code>/fspawnall [diya|bomb|fireworks|cracker]</code> — Force spawn in ALL groups\n\n"
        "⏱️ <b>Dynamic Economy & Cooldown Controls:</b>\n"
        "• <code>/setlootcooldown &lt;hours&gt;</code> — Change /loot cooldown (e.g. <code>/setlootcooldown 4</code>)\n"
        "• <code>/setlootcoins &lt;coins&gt;</code> — Change /loot reward (e.g. <code>/setlootcoins 12000</code>)\n"
        "• <code>/setdailycoins &lt;coins&gt;</code> — Change /daily reward (e.g. <code>/setdailycoins 5000</code>)\n"
        "• <code>/setgroupmin &lt;count&gt;</code> — Change group message threshold (e.g. <code>/setgroupmin 5</code>)\n\n"
        "💰 <b>Admin Coin Controls:</b>\n"
        "• <code>/addcoins &lt;user/@user/reply&gt; &lt;amount&gt;</code> — Mint & grant coins to player\n"
        "• <code>/takecoins &lt;user/@user/reply&gt; &lt;amount&gt;</code> — Deduct coins from player\n"
        "• <code>/setcoins &lt;user/@user/reply&gt; &lt;amount&gt;</code> — Set exact coin balance\n\n"
        "📊 <b>User & Bot Information:</b>\n"
        "• <code>/users</code> — Paginated directory of all registered players\n"
        "• <code>/userinfo &lt;user/@user/reply&gt;</code> — Detailed player dossier, balances & inventory\n"
        "• <code>/botinfo</code> — System diagnostics, storage engine & circulation metrics\n"
        "• <code>/groups</code> — List all connected group chats & drop states\n\n"
        "📢 <b>Broadcast & Analytics:</b>\n"
        "• <code>/broadcast &lt;message&gt;</code> — Send global announcement to all users & groups\n"
        "• <code>/stats</code> — View live database statistics"
    )
    await update.effective_message.reply_text(admin_text, parse_mode="HTML")

async def force_drop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /fdrop <coins> [max_claims] in current chat."""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not is_admin(user.id):
        return

    if not context.args:
        await update.effective_message.reply_text("Usage: <code>/fdrop &lt;coins&gt; [max_claims]</code>", parse_mode="HTML")
        return

    try:
        coins = int(context.args[0])
        max_claims = int(context.args[1]) if len(context.args) > 1 else 1
    except ValueError:
        await update.effective_message.reply_text("❌ Please provide valid integer numbers for coins and slots.")
        return

    await spawn_interactive_drop(chat.id, context, custom_coins=coins, max_claims=max_claims)
    await update.effective_message.reply_text(f"✅ Interactive drop created with {format_number(coins)} coins for {max_claims} player(s)!")

async def force_drop_all_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /fdropall <coins> [max_claims] across all registered groups."""
    user = update.effective_user
    if not user or not is_admin(user.id):
        return

    if not context.args:
        await update.effective_message.reply_text("Usage: <code>/fdropall &lt;coins&gt; [max_claims]</code>", parse_mode="HTML")
        return

    try:
        coins = int(context.args[0])
        max_claims = int(context.args[1]) if len(context.args) > 1 else 1
    except ValueError:
        await update.effective_message.reply_text("❌ Please provide valid numbers.")
        return

    groups = await db.get_all_groups()
    if not groups:
        await update.effective_message.reply_text("No groups registered yet.")
        return

    sent = 0
    status_msg = await update.effective_message.reply_text(f"⏳ Dropping in {len(groups)} groups...")

    for g in groups:
        try:
            await spawn_interactive_drop(g["chat_id"], context, custom_coins=coins, max_claims=max_claims)
            sent += 1
            await asyncio.sleep(0.1)  # Avoid rate limits
        except Exception:
            pass

    await status_msg.edit_text(f"✅ Successfully dispatched festive drop to {sent}/{len(groups)} groups!")

async def force_drop_custom_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /fdrop_custom <coins> | <slots> | <button_text> | <image_url> | <message>
    Pipe-delimited full control over drop!
    """
    user = update.effective_user
    chat = update.effective_chat
    if not user or not is_admin(user.id):
        return

    full_arg = " ".join(context.args)
    if not full_arg or "|" not in full_arg:
        syntax = (
            "<b>Usage for /fdrop_custom:</b>\n"
            "<code>/fdrop_custom coins | slots | button_text | image_url | custom_message</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/fdrop_custom 25000 | 2 | 🪔 Light Shubh Diya | https://images.unsplash.com/photo-1605649487212-47bdab064df8 | Royal Shagun arrived! Be the first to grab 25k coins!</code>"
        )
        await update.effective_message.reply_text(syntax, parse_mode="HTML")
        return

    parts = [p.strip() for p in full_arg.split("|")]
    try:
        coins = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 5000
        slots = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
        btn_text = parts[2] if len(parts) > 2 and parts[2] else f"🎁 Claim {format_number(coins)} Coins!"
        img_url = parts[3] if len(parts) > 3 and parts[3].startswith("http") else ""
        custom_msg = parts[4] if len(parts) > 4 and parts[4] else ""
    except Exception as e:
        await update.effective_message.reply_text(f"❌ Error parsing parameters: {e}")
        return

    await spawn_interactive_drop(
        chat.id,
        context,
        custom_coins=coins,
        custom_msg=custom_msg,
        custom_img=img_url,
        custom_btn=btn_text,
        max_claims=slots
    )
    await update.effective_message.reply_text("✅ Custom drop dispatched successfully!")

async def force_spawn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /fspawn [diya|bomb|fireworks|cracker] in current chat."""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not is_admin(user.id):
        return

    event_type = context.args[0].lower() if context.args else "bomb"
    await spawn_festive_burst(chat.id, context, event_type=event_type)
    await update.effective_message.reply_text(f"✅ Spawned '{event_type}' event in this group!")

async def force_spawn_all_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /fspawnall [diya|bomb|fireworks|cracker] in all groups."""
    user = update.effective_user
    if not user or not is_admin(user.id):
        return

    event_type = context.args[0].lower() if context.args else "fireworks"
    groups = await db.get_all_groups()
    sent = 0
    for g in groups:
        try:
            await spawn_festive_burst(g["chat_id"], context, event_type=event_type)
            sent += 1
            await asyncio.sleep(0.1)
        except Exception:
            pass
    await update.effective_message.reply_text(f"✅ Spawned '{event_type}' festive burst in {sent} groups!")

async def set_loot_cooldown_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setlootcooldown <hours>."""
    user = update.effective_user
    if not user or not is_admin(user.id):
        return

    if not context.args:
        current = await db.get_setting("loot_cooldown_hours", config.DEFAULT_LOOT_COOLDOWN_HOURS)
        await update.effective_message.reply_text(f"Current /loot cooldown: <b>{current}</b> hours.\nTo change: <code>/setlootcooldown &lt;hours&gt;</code>", parse_mode="HTML")
        return

    try:
        hours = float(context.args[0])
        if hours < 0:
            raise ValueError()
    except ValueError:
        await update.effective_message.reply_text("❌ Please provide a valid positive number for hours.")
        return

    await db.set_setting("loot_cooldown_hours", hours)
    await update.effective_message.reply_text(f"✅ <b>/loot cooldown updated to {hours} hours!</b>", parse_mode="HTML")

async def set_loot_coins_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setlootcoins <coins>."""
    user = update.effective_user
    if not user or not is_admin(user.id):
        return

    if not context.args or not context.args[0].isdigit():
        current = await db.get_setting("loot_coins", config.DEFAULT_LOOT_COINS)
        await update.effective_message.reply_text(f"Current /loot reward: <b>{format_number(current)}</b> coins.\nTo change: <code>/setlootcoins &lt;coins&gt;</code>", parse_mode="HTML")
        return

    coins = int(context.args[0])
    await db.set_setting("loot_coins", coins)
    await update.effective_message.reply_text(f"✅ <b>/loot reward updated to {format_number(coins)} coins!</b>", parse_mode="HTML")

async def set_daily_coins_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setdailycoins <coins>."""
    user = update.effective_user
    if not user or not is_admin(user.id):
        return

    if not context.args or not context.args[0].isdigit():
        current = await db.get_setting("daily_coins", config.DAILY_COINS)
        await update.effective_message.reply_text(f"Current /daily reward: <b>{format_number(current)}</b> coins.\nTo change: <code>/setdailycoins &lt;coins&gt;</code>", parse_mode="HTML")
        return

    coins = int(context.args[0])
    await db.set_setting("daily_coins", coins)
    await update.effective_message.reply_text(f"✅ <b>/daily reward updated to {format_number(coins)} coins!</b>", parse_mode="HTML")

async def set_group_min_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setgroupmin <count> for current chat."""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not is_admin(user.id):
        return

    if chat.type not in ["group", "supergroup"]:
        await update.effective_message.reply_text("This command can only be used in a group chat.")
        return

    if not context.args or not context.args[0].isdigit():
        await update.effective_message.reply_text("Usage: <code>/setgroupmin &lt;messages_count&gt;</code>", parse_mode="HTML")
        return

    count = int(context.args[0])
    await db.update_group(chat.id, {"min_messages": count})
    await update.effective_message.reply_text(f"✅ Group auto-spawn message threshold set to <b>{count}</b> messages!", parse_mode="HTML")

async def add_coins_admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /addcoins <target> <amount> (or /givecoins for admins).
    Mints new coins directly into the target user's account without deducting from admin.
    Supports reply to message, @username, or numeric user_id.
    """
    user = update.effective_user
    msg = update.effective_message
    if not user or not is_admin(user.id) or not msg:
        return

    target_id, target_name = await resolve_target_user(update, context)
    amount_str = None
    if len(context.args) >= 2:
        if context.args[1].isdigit():
            amount_str = context.args[1]
        elif context.args[0].isdigit():
            amount_str = context.args[0]
    elif len(context.args) == 1 and msg.reply_to_message:
        amount_str = context.args[0]

    if not target_id or not amount_str or not amount_str.isdigit():
        await msg.reply_text(
            "👑 <b>ADMIN COIN INJECTION (ADD COINS):</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Mints and grants coins directly to a player's balance.\n\n"
            "<b>Usage:</b>\n"
            "• <b>Reply</b> to a user's message: <code>/addcoins &lt;amount&gt;</code>\n"
            "• Or type: <code>/addcoins @username &lt;amount&gt;</code>\n"
            "• Or type: <code>/addcoins &lt;user_id&gt; &lt;amount&gt;</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/addcoins 50000</code> <i>(replying to user)</i>\n"
            "<code>/addcoins @username 25000</code>",
            parse_mode="HTML"
        )
        return

    amount = int(amount_str)
    new_bal = await db.add_coins(target_id, amount)
    target_user = await db.get_user(target_id)
    mention = get_mention(target_user, custom_title=target_name)

    await msg.reply_text(
        f"✅ <b>ADMIN COINS GRANTED!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>Target:</b> {mention} (ID: <code>{target_id}</code>)\n"
        f"🪙 <b>Added:</b> +<code>{format_number(amount)}</code> Coins\n"
        f"💰 <b>Updated Balance:</b> <code>{format_number(new_bal)}</code> Coins.",
        parse_mode="HTML"
    )

async def take_coins_admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /takecoins <target> <amount> (or /deductcoins for admins).
    Deducts coins from a player's balance.
    Supports reply to message, @username, or numeric user_id.
    """
    user = update.effective_user
    msg = update.effective_message
    if not user or not is_admin(user.id) or not msg:
        return

    target_id, target_name = await resolve_target_user(update, context)
    amount_str = None
    if len(context.args) >= 2:
        if context.args[1].isdigit():
            amount_str = context.args[1]
        elif context.args[0].isdigit():
            amount_str = context.args[0]
    elif len(context.args) == 1 and msg.reply_to_message:
        amount_str = context.args[0]

    if not target_id or not amount_str or not amount_str.isdigit():
        await msg.reply_text(
            "👑 <b>ADMIN COIN DEDUCTION (TAKE COINS):</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Deducts coins from a player's balance.\n\n"
            "<b>Usage:</b>\n"
            "• <b>Reply</b> to a user's message: <code>/takecoins &lt;amount&gt;</code>\n"
            "• Or type: <code>/takecoins @username &lt;amount&gt;</code>\n"
            "• Or type: <code>/takecoins &lt;user_id&gt; &lt;amount&gt;</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/takecoins 10000</code> <i>(replying to user)</i>\n"
            "<code>/takecoins @username 5000</code>",
            parse_mode="HTML"
        )
        return

    amount = int(amount_str)
    await db.deduct_coins(target_id, amount)
    target_user = await db.get_user(target_id)
    new_bal = target_user.get("coins", 0)
    mention = get_mention(target_user, custom_title=target_name)

    await msg.reply_text(
        f"⚠️ <b>ADMIN COINS DEDUCTED!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>Target:</b> {mention} (ID: <code>{target_id}</code>)\n"
        f"🪙 <b>Deducted:</b> -<code>{format_number(amount)}</code> Coins\n"
        f"💰 <b>Updated Balance:</b> <code>{format_number(new_bal)}</code> Coins.",
        parse_mode="HTML"
    )

async def set_coins_admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /setcoins <target> <exact_amount>.
    Sets a player's balance to an exact amount.
    """
    user = update.effective_user
    msg = update.effective_message
    if not user or not is_admin(user.id) or not msg:
        return

    target_id, target_name = await resolve_target_user(update, context)
    amount_str = None
    if len(context.args) >= 2:
        if context.args[1].isdigit():
            amount_str = context.args[1]
        elif context.args[0].isdigit():
            amount_str = context.args[0]
    elif len(context.args) == 1 and msg.reply_to_message:
        amount_str = context.args[0]

    if not target_id or not amount_str or not amount_str.isdigit():
        await msg.reply_text(
            "👑 <b>ADMIN SET EXACT BALANCE (/setcoins):</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Sets a player's coins balance to an exact value.\n\n"
            "<b>Usage:</b>\n"
            "• <b>Reply</b> to a user's message: <code>/setcoins &lt;amount&gt;</code>\n"
            "• Or type: <code>/setcoins @username &lt;amount&gt;</code>\n"
            "• Or type: <code>/setcoins &lt;user_id&gt; &lt;amount&gt;</code>",
            parse_mode="HTML"
        )
        return

    new_amount = int(amount_str)
    await db.update_user(target_id, {"coins": new_amount})
    target_user = await db.get_user(target_id)
    mention = get_mention(target_user, custom_title=target_name)

    await msg.reply_text(
        f"⚙️ <b>ADMIN BALANCE OVERWRITE!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>Target:</b> {mention} (ID: <code>{target_id}</code>)\n"
        f"💰 <b>Exact Balance Set To:</b> <code>{format_number(new_amount)}</code> Coins.",
        parse_mode="HTML"
    )

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast <message>."""
    user = update.effective_user
    if not user or not is_admin(user.id):
        return

    if not context.args:
        await update.effective_message.reply_text("Usage: <code>/broadcast &lt;message text&gt;</code>", parse_mode="HTML")
        return

    b_text = " ".join(context.args)
    formatted_msg = (
        f"📢 <b>FESTIVE BROADCAST ANNOUNCEMENT</b> 📢\n\n"
        f"{b_text}\n\n"
        f"✨ <i>Wishing everyone a blessed and prosperous Diwali!</i> 🪔"
    )

    users = await db.get_all_users()
    groups = await db.get_all_groups()

    all_targets = set([u["user_id"] for u in users] + [g["chat_id"] for g in groups])
    status = await update.effective_message.reply_text(f"⏳ Broadcasting to {len(all_targets)} destinations...")

    success = 0
    for target in all_targets:
        try:
            await context.bot.send_message(chat_id=target, text=formatted_msg, parse_mode="HTML")
            success += 1
            await asyncio.sleep(0.08)
        except Exception:
            pass

    await status.edit_text(f"✅ Broadcast finished! Delivered to <b>{success}/{len(all_targets)}</b> chats.", parse_mode="HTML")

async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command."""
    user = update.effective_user
    if not user or not is_admin(user.id):
        return

    stats = await db.get_stats()
    text = (
        "📊 <b>DIWALI BOT LIVE METRICS</b> 📊\n\n"
        f"👥 <b>Total Users:</b> <code>{format_number(stats['total_users'])}</code>\n"
        f"👥 <b>Active Groups:</b> <code>{format_number(stats['total_groups'])}</code>\n"
        f"🪙 <b>Coins in Circulation:</b> <code>{format_number(stats['total_coins'])}</code>\n"
        f"💌 <b>Total Wishes Shared:</b> <code>{format_number(stats['total_wishes'])}</code>\n"
        f"🎁 <b>Total Gifts Sent:</b> <code>{format_number(stats['total_gifts'])}</code>\n"
        f"💾 <b>Database Mode:</b> <code>{stats['storage_mode']}</code>"
    )
    await update.effective_message.reply_text(text, parse_mode="HTML")

# --- Dynamic Image Management Handlers ---

async def add_image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /addimage <category> [url]
    Or reply to a photo with: /addimage <category>
    """
    user = update.effective_user
    msg = update.effective_message
    if not user or not is_admin(user.id) or not msg:
        return

    if not context.args:
        cats_str = ", ".join(VALID_IMAGE_CATEGORIES)
        await msg.reply_text(
            f"<b>Usage:</b>\n"
            f"• <code>/addimage &lt;category&gt; &lt;url&gt;</code>\n"
            f"• Or reply to a photo with <code>/addimage &lt;category&gt;</code>\n\n"
            f"<b>Valid Categories:</b>\n<code>{cats_str}</code>",
            parse_mode="HTML"
        )
        return

    category = context.args[0].lower()
    if category not in VALID_IMAGE_CATEGORIES:
        cats_str = ", ".join(VALID_IMAGE_CATEGORIES)
        await msg.reply_text(f"❌ Invalid category '{category}'.\nValid options: <code>{cats_str}</code>", parse_mode="HTML")
        return

    image_source = None

    # Check if replied to a photo
    if msg.reply_to_message and msg.reply_to_message.photo:
        # Use largest photo file_id
        image_source = msg.reply_to_message.photo[-1].file_id
    elif len(context.args) > 1:
        image_source = context.args[1].strip()

    if not image_source:
        await msg.reply_text("❌ Please provide an image URL or reply to a photo!")
        return

    total = await add_custom_image(category, image_source)
    await msg.reply_text(
        f"✅ <b>Image added to '{category}'!</b>\n"
        f"Total images in this category: <b>{total}</b>\n\n"
        f"Now whenever <code>/{category}</code> or random GC spawns trigger, this image will be part of the rotation! 🪔",
        parse_mode="HTML"
    )

async def del_image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /delimage <category> <1-based index>."""
    user = update.effective_user
    msg = update.effective_message
    if not user or not is_admin(user.id) or not msg:
        return

    if len(context.args) < 2 or not context.args[1].isdigit():
        await msg.reply_text("Usage: <code>/delimage &lt;category&gt; &lt;image_index&gt;</code>\nCheck index using <code>/listimages &lt;category&gt;</code>", parse_mode="HTML")
        return

    category = context.args[0].lower()
    idx = int(context.args[1]) - 1

    success = await remove_custom_image(category, idx)
    if success:
        await msg.reply_text(f"✅ Image #{idx + 1} deleted from category '{category}'.")
    else:
        await msg.reply_text(f"❌ Invalid index or no custom images found for '{category}'.")

CATEGORY_METADATA = {
    "diya": {
        "title": "🪔 Diya Illuminations",
        "desc": "Used in <code>/diya</code> command & random holy diya spawns in group chats."
    },
    "diwali": {
        "title": "💥 Diwali Cracker Burst",
        "desc": "Used in <code>/diwali</code> command & patakha celebrations in group chats."
    },
    "bomb": {
        "title": "💣 Sutli Bomb Explosion",
        "desc": "Used in high-intensity bomb bursts and group activity explosions."
    },
    "fireworks": {
        "title": "🎆 Sky Fireworks Display",
        "desc": "Used in midnight fireworks celebration and festive bursts."
    },
    "wish": {
        "title": "💌 Festive Greeting Cards",
        "desc": "Used in <code>/wish</code> command when users send greetings to friends."
    },
    "mithai": {
        "title": "🍬 Mithai & Sweets Feed",
        "desc": "Used in <code>/mithai</code> command when friends share sweet treats."
    },
    "loot_drop": {
        "title": "🎁 Group Treasure Chests",
        "desc": "Used in interactive group coin drops & <code>/fdrop</code> treasure chests."
    },
    "welcome": {
        "title": "🌟 Start & Welcome Banner",
        "desc": "Header image for <code>/start</code> welcome menu and intro card."
    },
    "daily": {
        "title": "🪙 Daily Reward Banner",
        "desc": "Header card shown when players claim their <code>/daily</code> coins."
    },
    "loot": {
        "title": "💰 Periodic Loot Vault",
        "desc": "Header banner displayed during <code>/loot</code> claims."
    }
}

async def generate_categories_overview() -> tuple[str, InlineKeyboardMarkup]:
    """Generate overview of all image categories with descriptions & 1-tap buttons."""
    lines = [
        "🖼️ <b>DIWALI BOT — IMAGE CATEGORIES DIRECTORY</b> 🖼️",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "<i>Admins can add custom images or photo uploads to any category below. The bot rotates them automatically in commands and group events!</i>\n"
    ]

    buttons = []
    current_row = []

    for idx, cat in enumerate(VALID_IMAGE_CATEGORIES, start=1):
        meta = CATEGORY_METADATA.get(cat, {"title": cat.capitalize(), "desc": "Custom festive images."})
        imgs = await get_category_images(cat)
        img_count = len(imgs)

        lines.append(
            f"<b>{idx}. <code>{cat}</code></b> — {meta['title']}\n"
            f"   ├ 📝 <i>{meta['desc']}</i>\n"
            f"   └ 🖼️ <b>{img_count}</b> active image(s)"
        )

        short_title = meta["title"].split(" ")[0] + " " + cat
        current_row.append(InlineKeyboardButton(short_title, callback_data=f"cat_inspect:{cat}"))
        if len(current_row) == 2:
            buttons.append(current_row)
            current_row = []

    if current_row:
        buttons.append(current_row)

    lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("<b>📥 How to Add an Image:</b>")
    lines.append("• <b>Upload:</b> Reply to any photo in chat with <code>/addimage &lt;category&gt;</code>")
    lines.append("• <b>URL:</b> Type <code>/addimage &lt;category&gt; &lt;url&gt;</code>\n")
    lines.append("<b>💡 Tips:</b> Tap any button below to view active image URLs/IDs or delete images!")

    buttons.append([
        InlineKeyboardButton("🔄 Refresh Categories", callback_data="admin_view_cats"),
        InlineKeyboardButton("🏠 Admin Menu", callback_data="help_admin")
    ])

    return "\n".join(lines), InlineKeyboardMarkup(buttons)

async def generate_category_detail(cat: str) -> tuple[str, InlineKeyboardMarkup]:
    """Generate detailed breakdown of images inside a specific category."""
    if cat not in VALID_IMAGE_CATEGORIES:
        return f"❌ Invalid category '{cat}'. Use <code>/categories</code> to see valid options.", InlineKeyboardMarkup([[InlineKeyboardButton("🔙 All Categories", callback_data="admin_view_cats")]])

    meta = CATEGORY_METADATA.get(cat, {"title": cat.capitalize(), "desc": "Custom images category."})
    imgs = await get_category_images(cat)

    lines = [
        f"🖼️ <b>CATEGORY: {meta['title']} (<code>{cat}</code>)</b>",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📝 <i>{meta['desc']}</i>",
        f"📊 <b>Active Images Count:</b> <code>{len(imgs)}</code>\n"
    ]

    if not imgs:
        lines.append("<i>No images configured yet for this category.</i>\n")
    else:
        for i, img in enumerate(imgs):
            display = img[:60] + "..." if len(img) > 60 else img
            lines.append(f"<b>#{i+1}:</b> <code>{display}</code>")

    lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("<b>📥 To Add an Image:</b>")
    lines.append(f"• Reply to any Telegram photo with: <code>/addimage {cat}</code>")
    lines.append(f"• Or enter URL: <code>/addimage {cat} &lt;image_url&gt;</code>")
    lines.append("\n<b>🗑️ To Delete an Image:</b>")
    lines.append(f"• <code>/delimage {cat} &lt;index&gt;</code> (e.g. <code>/delimage {cat} 1</code>)")
    lines.append(f"• Reset to defaults: <code>/resetimages {cat}</code>")

    buttons = [
        [InlineKeyboardButton("🔙 Back to All Categories", callback_data="admin_view_cats")],
        [InlineKeyboardButton("🔄 Refresh Category", callback_data=f"cat_inspect:{cat}")]
    ]
    return "\n".join(lines), InlineKeyboardMarkup(buttons)

async def list_categories_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /categories, /imagecategories, /imgcategories, or /cats (Admin only)."""
    user = update.effective_user
    msg = update.effective_message
    if not user or not msg:
        return

    if not is_admin(user.id):
        await msg.reply_text("⛔ Access Denied: Administrator privileges required.")
        return

    if context.args:
        cat = context.args[0].lower()
        text, markup = await generate_category_detail(cat)
        await msg.reply_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        text, markup = await generate_categories_overview()
        await msg.reply_text(text, parse_mode="HTML", reply_markup=markup)

async def list_images_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /listimages [category]."""
    user = update.effective_user
    msg = update.effective_message
    if not user or not is_admin(user.id) or not msg:
        return

    if context.args:
        cat = context.args[0].lower()
        text, markup = await generate_category_detail(cat)
        await msg.reply_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        text, markup = await generate_categories_overview()
        await msg.reply_text(text, parse_mode="HTML", reply_markup=markup)

async def reset_images_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /resetimages [category]."""
    user = update.effective_user
    msg = update.effective_message
    if not user or not is_admin(user.id) or not msg:
        return

    cat = context.args[0].lower() if context.args else None
    await reset_custom_images(cat)
    if cat:
        await msg.reply_text(f"✅ Category '{cat}' has been reset to default config images.")
    else:
        await msg.reply_text("✅ All image categories have been reset to default config images.")

# --- Dynamic Admin Management Handlers ---

async def add_admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /addadmin <user_id or reply or @username>
    Only permanent bot owners (from config.ADMIN_IDS) can promote new admins!
    """
    user = update.effective_user
    msg = update.effective_message
    if not user or not msg:
        return

    # Check if sender is owner
    if not is_owner(user.id):
        await msg.reply_text("⛔ Access Denied: Only the permanent Bot Owner can appoint new admins.")
        return

    target_id, target_name = await resolve_target_user(update, context)
    if not target_id:
        await msg.reply_text(
            "<b>Usage:</b>\n"
            "• Reply to someone's message with <code>/addadmin</code>\n"
            "• Or type <code>/addadmin &lt;user_id&gt;</code>\n"
            "• Or type <code>/addadmin @username</code>",
            parse_mode="HTML"
        )
        return

    if is_admin(target_id):
        await msg.reply_text(f"⚠️ User <code>{target_id}</code> is already an administrator.")
        return

    target_user = await db.get_user(target_id)
    success = await add_dynamic_admin(target_id)
    if success:
        mention = get_mention(target_user, custom_title=target_name)
        await msg.reply_text(
            f"🎉 <b>NEW ADMIN APPOINTED!</b> 🛡️\n\n"
            f"User {mention} (ID: <code>{target_id}</code>) has been promoted to <b>Bot Administrator</b>!\n"
            f"They now have full access to admin commands and controls.",
            parse_mode="HTML"
        )
    else:
        await msg.reply_text("❌ Failed to add admin. Please try again.")

async def del_admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /deladmin <user_id or reply or @username>
    Only permanent bot owners can remove admins.
    """
    user = update.effective_user
    msg = update.effective_message
    if not user or not msg:
        return

    if not is_owner(user.id):
        await msg.reply_text("⛔ Access Denied: Only the permanent Bot Owner can remove admins.")
        return

    target_id, target_name = await resolve_target_user(update, context)
    if not target_id:
        await msg.reply_text(
            "<b>Usage:</b>\n"
            "• Reply to someone's message with <code>/deladmin</code>\n"
            "• Or type <code>/deladmin &lt;user_id&gt;</code>\n"
            "• Or type <code>/deladmin @username</code>",
            parse_mode="HTML"
        )
        return

    if is_owner(target_id):
        await msg.reply_text("❌ You cannot remove a permanent Bot Owner defined in the bot configuration!")
        return

    target_user = await db.get_user(target_id)
    success = await remove_dynamic_admin(target_id)
    if success:
        mention = get_mention(target_user, custom_title=target_name)
        await msg.reply_text(
            f"🗑️ <b>ADMIN DEMOTED!</b>\n\n"
            f"User {mention} (ID: <code>{target_id}</code>) has been removed from Bot Administrators.",
            parse_mode="HTML"
        )
    else:
        await msg.reply_text(f"❌ User <code>{target_id}</code> is not in the dynamic administrators list.")

async def list_admins_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /admins or /listadmins
    Shows permanent owners and dynamically added admins.
    """
    user = update.effective_user
    msg = update.effective_message
    if not user or not is_admin(user.id) or not msg:
        return

    all_adm_ids = await get_all_admins()
    lines = ["🛡️ <b>BOT ADMINISTRATORS & OWNERS</b> 🛡️\n"]

    for uid in all_adm_ids:
        u_doc = await db.get_user(uid)
        role = "👑 Owner" if is_owner(uid) else "🛡️ Admin"
        name = u_doc.get("first_name", "User")
        uname = f"(@{u_doc.get('username')})" if u_doc.get("username") else ""
        lines.append(f"• {role} — <b>{name}</b> {uname} [<code>{uid}</code>]")

    lines.append("\n<i>Only permanent Bot Owners can /addadmin or /deladmin.</i>")
    await msg.reply_text("\n".join(lines), parse_mode="HTML")

# --- Users Directory & Pagination ---
PAGE_SIZE = 8

async def generate_users_directory(page: int = 1) -> tuple[str, InlineKeyboardMarkup]:
    """Generate paginated directory of registered players."""
    users = await db.get_all_users()
    total_users = len(users)
    if total_users == 0:
        return "👥 <b>No registered players found in database yet.</b>", InlineKeyboardMarkup([])

    # Sort by coins descending
    users.sort(key=lambda u: u.get("coins", 0), reverse=True)

    total_pages = max(1, (total_users + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * PAGE_SIZE
    page_users = users[start_idx : start_idx + PAGE_SIZE]

    all_admins = await get_all_admins()

    lines = [
        "👥 <b>REGISTERED PLAYERS DIRECTORY</b> 👥",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📊 <b>Total Registered:</b> <code>{total_users}</code> | 📄 <b>Page:</b> <code>{page}/{total_pages}</code>\n"
    ]

    for idx, u in enumerate(page_users, start=start_idx + 1):
        uid = u.get("user_id", 0)
        first_name = (u.get("first_name") or "User").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        uname = f"(@{u.get('username')})" if u.get("username") else ""
        coins = format_number(u.get("coins", 0))

        if is_owner(uid):
            role_badge = "👑 Owner"
        elif uid in all_admins:
            role_badge = "🛡️ Admin"
        else:
            role_badge = "👤 Player"

        lines.append(
            f"<b>{idx}.</b> <a href=\"tg://user?id={uid}\">{first_name}</a> {uname}\n"
            f"   ├ 🆔 <code>{uid}</code>\n"
            f"   ├ 💰 <b>{coins}</b> Coins | {role_badge}\n"
            f"   └ 🎁 Gifts Sent: <code>{u.get('gifts_sent', 0)}</code> | 💌 Wishes: <code>{u.get('wishes_sent', 0)}</code>"
        )

    lines.append("\n<i>💡 Tip: Use <code>/userinfo &lt;id&gt;</code> to inspect any player's full dossier.</i>")

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"users_page:{page - 1}"))
    nav_buttons.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data=f"users_page:{page}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"users_page:{page + 1}"))

    action_buttons = [
        InlineKeyboardButton("🔄 Refresh", callback_data=f"users_page:{page}"),
        InlineKeyboardButton("🏰 View Groups", callback_data="groups_page:1")
    ]

    markup = InlineKeyboardMarkup([nav_buttons, action_buttons])
    return "\n".join(lines), markup

async def users_list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /users or /listusers (Admin only)."""
    user = update.effective_user
    msg = update.effective_message
    if not user or not msg:
        return

    if not is_admin(user.id):
        await msg.reply_text("⛔ Access Denied: Administrator privileges required.")
        return

    text, markup = await generate_users_directory(page=1)
    await msg.reply_text(text, parse_mode="HTML", reply_markup=markup, disable_web_page_preview=True)

# --- Group Chats Directory & Pagination ---
GROUP_PAGE_SIZE = 8

async def generate_groups_directory(page: int = 1) -> tuple[str, InlineKeyboardMarkup]:
    """Generate paginated list of connected group chats."""
    groups = await db.get_all_groups()
    total_groups = len(groups)
    if total_groups == 0:
        return (
            "🏰 <b>No registered groups found in database yet.</b>\n"
            "<i>Add the bot to a group and grant admin permissions to track chat activity!</i>",
            InlineKeyboardMarkup([])
        )

    groups.sort(key=lambda g: g.get("message_count", 0), reverse=True)

    total_pages = max(1, (total_groups + GROUP_PAGE_SIZE - 1) // GROUP_PAGE_SIZE)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * GROUP_PAGE_SIZE
    page_groups = groups[start_idx : start_idx + GROUP_PAGE_SIZE]

    lines = [
        "🏰 <b>REGISTERED GROUP DIRECTORY</b> 🏰",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📊 <b>Total Connected Groups:</b> <code>{total_groups}</code> | 📄 <b>Page:</b> <code>{page}/{total_pages}</code>\n"
    ]

    for idx, g in enumerate(page_groups, start=start_idx + 1):
        cid = g.get("chat_id", 0)
        title = (g.get("title") or "Unnamed Group").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        msg_count = g.get("message_count", 0)
        min_msgs = g.get("min_messages", config.DEFAULT_MIN_GROUP_MESSAGES)
        drops_active = "✅ Active" if g.get("drops_enabled", True) else "❌ Muted"

        lines.append(
            f"<b>{idx}. {title}</b>\n"
            f"   ├ 🆔 Chat ID: <code>{cid}</code>\n"
            f"   ├ 💬 Messages: <b>{msg_count}/{min_msgs}</b> msgs to drop\n"
            f"   └ 🎁 Drops Status: {drops_active}"
        )

    lines.append("\n<i>💡 Tip: Use <code>/fdrop 5000</code> or <code>/fspawn bomb</code> inside any group!</i>")

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"groups_page:{page - 1}"))
    nav_buttons.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data=f"groups_page:{page}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"groups_page:{page + 1}"))

    action_buttons = [
        InlineKeyboardButton("🔄 Refresh", callback_data=f"groups_page:{page}"),
        InlineKeyboardButton("👥 View Players", callback_data="users_page:1")
    ]

    markup = InlineKeyboardMarkup([nav_buttons, action_buttons])
    return "\n".join(lines), markup

async def groups_list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /groups or /listgroups (Admin only)."""
    user = update.effective_user
    msg = update.effective_message
    if not user or not msg:
        return

    if not is_admin(user.id):
        await msg.reply_text("⛔ Access Denied: Administrator privileges required.")
        return

    text, markup = await generate_groups_directory(page=1)
    await msg.reply_text(text, parse_mode="HTML", reply_markup=markup)

# --- Detailed User Info Dossier ---
async def user_info_admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /userinfo <user/@user/reply> or /uinfo
    Shows complete dossier of player's balance, inventory, rank, role, timestamps.
    """
    user = update.effective_user
    msg = update.effective_message
    if not user or not msg:
        return

    if not is_admin(user.id):
        await msg.reply_text("⛔ Access Denied: Administrator privileges required.")
        return

    target_id = None
    target_name = None

    if msg.reply_to_message and msg.reply_to_message.from_user:
        target = msg.reply_to_message.from_user
        if not target.is_bot:
            target_id = target.id
            target_name = target.first_name
    elif context.args and len(context.args) > 0:
        target_id, target_name = await resolve_target_user(update, context)
        if not target_id:
            await msg.reply_text(
                "❌ <b>Target user not found!</b>\n\n"
                "<b>Usage:</b>\n"
                "• Reply to any user message with <code>/userinfo</code>\n"
                "• Or type <code>/userinfo &lt;user_id&gt;</code>\n"
                "• Or type <code>/userinfo @username</code>",
                parse_mode="HTML"
            )
            return
    else:
        target_id = user.id
        target_name = user.first_name

    u_doc = await db.get_user(target_id)
    if not u_doc:
        await msg.reply_text(f"❌ User <code>{target_id}</code> is not registered in the database.", parse_mode="HTML")
        return

    first_name = (u_doc.get("first_name") or target_name or "Player").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    uname = f"@{u_doc.get('username')}" if u_doc.get("username") else "<i>None</i>"
    coins = format_number(u_doc.get("coins", 0))

    all_admins = await get_all_admins()
    if is_owner(target_id):
        role_str = "👑 <b>Permanent Bot Owner</b>"
    elif target_id in all_admins:
        role_str = "🛡️ <b>Bot Administrator</b>"
    else:
        role_str = "👤 <b>Festive Diwali Player</b>"

    all_users = await db.get_all_users()
    all_users.sort(key=lambda x: x.get("coins", 0), reverse=True)
    rank = 1
    for i, u in enumerate(all_users, start=1):
        if u.get("user_id") == target_id:
            rank = i
            break

    theme = u_doc.get("theme", "royal").capitalize()

    inv = u_doc.get("inventory", {})
    ladoo = inv.get("ladoo", 0)
    kaju = inv.get("kaju_katli", 0)
    phuljhadi = inv.get("phuljhadi", 0)
    anar = inv.get("anar", 0)
    rocket = inv.get("rocket_box", 0)
    laxmi = inv.get("laxmi_bomb", 0)
    gold = inv.get("gold_coin", 0)

    wishes = u_doc.get("wishes_sent", 0)
    mithai = u_doc.get("mithai_sent", 0)
    gifts_sent = u_doc.get("gifts_sent", 0)
    gifts_recv = u_doc.get("gifts_received", 0)
    joined = u_doc.get("created_at", "N/A")
    if joined != "N/A" and "T" in str(joined):
        joined = str(joined).split("T")[0]

    last_daily = u_doc.get("last_daily")
    ready_daily, rem_daily = check_cooldown(last_daily, 24 * 3600)
    daily_status = "✅ <b>Ready Now!</b>" if ready_daily else f"⏳ In {format_remaining_time(rem_daily)}"

    loot_cd_hrs = await db.get_setting("loot_cooldown_hours", config.DEFAULT_LOOT_COOLDOWN_HOURS)
    last_loot = u_doc.get("last_loot")
    ready_loot, rem_loot = check_cooldown(last_loot, int(loot_cd_hrs * 3600))
    loot_status = "✅ <b>Ready Now!</b>" if ready_loot else f"⏳ In {format_remaining_time(rem_loot)}"

    last_diya = u_doc.get("last_diya")
    ready_diya, rem_diya = check_cooldown(last_diya, config.DIYA_COOLDOWN_SECONDS)
    diya_status = "✅ <b>Ready Now!</b>" if ready_diya else f"⏳ In {format_remaining_time(rem_diya)}"

    dossier = (
        f"📋 <b>PLAYER DOSSIER — USER INFO</b> 📋\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Name:</b> {first_name}\n"
        f"🔖 <b>Username:</b> {uname}\n"
        f"🆔 <b>Telegram ID:</b> <code>{target_id}</code>\n"
        f"🛡️ <b>Role:</b> {role_str}\n"
        f"🎨 <b>UI Font Theme:</b> <code>{theme}</code>\n\n"
        f"💰 <b>FINANCIAL STATUS:</b>\n"
        f"├ 🪙 Balance: <b>{coins} Coins</b>\n"
        f"└ 🏆 Wealth Rank: <b>#{rank}</b> of {len(all_users)} players\n\n"
        f"🎒 <b>INVENTORY COLLECTION:</b>\n"
        f"├ 🍬 Ladoo: <code>{ladoo}</code> | 🥮 Kaju Katli: <code>{kaju}</code>\n"
        f"├ 🎆 Phuljhadi: <code>{phuljhadi}</code> | 🌋 Anar: <code>{anar}</code>\n"
        f"├ 🚀 Rocket: <code>{rocket}</code> | 💣 Laxmi Bomb: <code>{laxmi}</code>\n"
        f"└ 🪙 Pure Gold Coin: <code>{gold}</code>\n\n"
        f"🎉 <b>FESTIVE ACTIVITY & STATS:</b>\n"
        f"├ 🪔 Diya Status: {diya_status}\n"
        f"├ 💌 Wishes Sent: <b>{wishes}</b>\n"
        f"├ 🍬 Mithai Shared: <b>{mithai}</b>\n"
        f"├ 🎁 Gifts Sent: <b>{gifts_sent}</b> | Received: <b>{gifts_recv}</b>\n"
        f"└ 📅 Registered: <code>{joined}</code>\n\n"
        f"⏳ <b>COOLDOWNS STATUS:</b>\n"
        f"├ 📆 Daily Reward: {daily_status}\n"
        f"└ 📦 Loot Reward: {loot_status}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>⚡ Quick Admin Commands:</i>\n"
        f"• <code>/addcoins {target_id} 5000</code>\n"
        f"• <code>/takecoins {target_id} 2000</code>\n"
        f"• <code>/setcoins {target_id} 10000</code>"
    )

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👥 All Players Directory", callback_data="users_page:1"),
            InlineKeyboardButton("📊 Bot Info", callback_data="admin_botinfo")
        ]
    ])

    await msg.reply_text(dossier, parse_mode="HTML", reply_markup=markup)

# --- Bot Info & System Diagnostics ---
async def get_bot_info_text(context: ContextTypes.DEFAULT_TYPE) -> tuple[str, InlineKeyboardMarkup]:
    """Generate overall bot diagnostics and status text."""
    bot_me = await context.bot.get_me()
    stats = await db.get_stats()
    all_admins = await get_all_admins()

    loot_hrs = await db.get_setting("loot_cooldown_hours", config.DEFAULT_LOOT_COOLDOWN_HOURS)
    loot_coins = await db.get_setting("loot_coins", config.DEFAULT_LOOT_COINS)
    daily_coins = await db.get_setting("daily_coins", config.DEFAULT_DAILY_COINS)
    group_min = await db.get_setting("min_group_messages", config.DEFAULT_MIN_GROUP_MESSAGES)

    uptime_sec = int((datetime.utcnow() - BOT_START_TIME).total_seconds())
    uptime_str = format_remaining_time(uptime_sec)

    custom_images = await db.get_setting("custom_images", {})
    custom_img_count = sum(len(v) for v in custom_images.values() if isinstance(v, list))

    text = (
        f"🤖 <b>DIWALI BOT — SYSTEM ARCHITECTURE & INFO</b> 🤖\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ <b>Bot Tag:</b> @{bot_me.username} ({bot_me.first_name})\n"
        f"👑 <b>Permanent Owner:</b> <code>{config.OWNER_ID}</code>\n"
        f"🛡️ <b>Total Admins:</b> <code>{len(all_admins)}</code>\n"
        f"⏱️ <b>Online Uptime:</b> <code>{uptime_str}</code>\n\n"
        f"🗄️ <b>DATABASE & STORAGE:</b>\n"
        f"├ ⚙️ Engine: <b>{stats['storage_mode']}</b>\n"
        f"├ 👥 Total Registered Users: <b>{format_number(stats['total_users'])}</b>\n"
        f"└ 🏰 Total Active Groups: <b>{format_number(stats['total_groups'])}</b>\n\n"
        f"💰 <b>ECONOMY & CIRCULATION:</b>\n"
        f"├ 🪙 Total Coins in Circulation: <b>{format_number(stats['total_coins'])}</b>\n"
        f"├ 🎁 Gifts Exchanged: <b>{format_number(stats['total_gifts'])}</b>\n"
        f"└ 💌 Wishes Shared: <b>{format_number(stats['total_wishes'])}</b>\n\n"
        f"⚙️ <b>CONFIGURED DYNAMICS:</b>\n"
        f"├ ⏰ Loot Cooldown: <b>{loot_hrs} Hours</b>\n"
        f"├ 💰 Loot Grant: <b>{format_number(loot_coins)} Coins</b>\n"
        f"├ 🪙 Daily Grant: <b>{format_number(daily_coins)} Coins</b>\n"
        f"├ 💬 Group Drop Threshold: <b>{group_min} msgs</b>\n"
        f"└ 🖼️ Custom Override Images: <b>{custom_img_count} Active</b>\n\n"
        f"🖥️ <b>SYSTEM RUNTIME:</b>\n"
        f"├ 🐍 Python: <code>{platform.python_version()}</code>\n"
        f"├ 📦 PTB Framework: <code>v21.11.1</code>\n"
        f"└ 💻 Platform: <code>{platform.system()} ({platform.release()})</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Status: All systems operational & running smoothly! 🪔</i>"
    )

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👥 Users Directory", callback_data="users_page:1"),
            InlineKeyboardButton("🏰 Connected Groups", callback_data="groups_page:1")
        ],
        [
            InlineKeyboardButton("🔄 Refresh Info", callback_data="admin_botinfo")
        ]
    ])
    return text, markup

async def bot_info_admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /botinfo or /info (Admin only)."""
    user = update.effective_user
    msg = update.effective_message
    if not user or not msg:
        return

    if not is_admin(user.id):
        await msg.reply_text("⛔ Access Denied: Administrator privileges required.")
        return

    text, markup = await get_bot_info_text(context)
    await msg.reply_text(text, parse_mode="HTML", reply_markup=markup)


