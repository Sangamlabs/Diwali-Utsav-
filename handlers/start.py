from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import config
from database import db
from utils import get_mention, format_number, get_random_image, is_admin

def get_welcome_text(user, coins: int) -> str:
    """Generate aesthetic welcome text."""
    mention = get_mention(user)
    coins_str = format_number(coins)
    return (
        f"✨ 🪔 <b>SHUBH DEEPAVALI, {mention}!</b> 🪔 ✨\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"May Goddess Lakshmi bestow endless wealth, peace, and eternal radiance upon you and your family!\n\n"
        f"🪙 <b>Your Shagun Balance:</b> <code>{coins_str}</code> Coins\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌟 <b>Quick Festive Shortcuts:</b>\n"
        f"• 🪔 <b>/diya</b> — Light sacred lamps & claim blessings\n"
        f"• 💥 <b>/diwali</b> — Ignite explosive night fireworks\n"
        f"• 🎁 <b>/gift</b> — Send festive sweets & gold coins to friends\n"
        f"• 🧧 <b>/lifafa</b> — Drop shagun packets in group chats\n"
        f"• 🎮 <b>/games</b> — Play Cracker Gamble, 3D Dice & Trivia\n"
        f"• 💰 <b>/daily</b> & <b>/loot</b> — Collect daily wealth\n\n"
        f"<i>Add me to your groups to unlock community diya milestones & automatic festive drops!</i>"
    )

def get_main_menu_keyboard(user_id: int, bot_username: str) -> InlineKeyboardMarkup:
    """Generate modern, clean inline menu buttons."""
    buttons = [
        [
            InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{bot_username}?startgroup=true"),
            InlineKeyboardButton("🎁 Gift Bazaar", callback_data="shop_view")
        ],
        [
            InlineKeyboardButton("🎮 Games Hub", callback_data="help_games"),
            InlineKeyboardButton("🎒 My Profile", callback_data="view_profile_quick")
        ],
        [
            InlineKeyboardButton("📜 Commands Guide", callback_data="help_user"),
            InlineKeyboardButton("🏆 Leaderboards", callback_data="lb_coins")
        ]
    ]
    if is_admin(user_id):
        buttons.append([InlineKeyboardButton("👑 Admin Control Center", callback_data="help_admin")])
    return InlineKeyboardMarkup(buttons)

def get_user_help_text() -> str:
    """Generate main command guide for regular users."""
    return (
        "🪔 <b>DIWALI BOT — FESTIVE COMMAND DIRECTORY</b> 🪔\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✨ <b>Festive Atmosphere:</b>\n"
        "• <code>/diya</code> — Light holy clay lamp & earn 200–600 coins <i>(60s cd)</i>\n"
        "• <code>/diwali</code> — Burst explosive fireworks & crackers <i>(20s cd)</i>\n"
        "• <code>/wish [reply/@user]</code> — Send personalized festive blessings\n"
        "• <code>/mithai [reply/@user]</code> — Share mouthwatering Indian sweets\n\n"
        "💰 <b>Economy & Wealth:</b>\n"
        "• <code>/daily</code> — Claim 5,000 coins daily festive bonus <i>(24h cd)</i>\n"
        "• <code>/loot</code> — Unlock treasure vault for 10,000 coins <i>(6h cd)</i>\n"
        "• <code>/pay [reply/@user] &lt;amount&gt;</code> — Transfer coins to friends as festive shagun\n"
        "• <code>/profile</code> or <code>/balance</code> — View coins, rank & gift inventory\n"
        "• <code>/theme</code> or <code>/font</code> — Aesthetic UI themes & mathematical font studio 🎨\n"
        "• <code>/top</code> — Live leaderboards for richest & most generous players\n\n"
        "🎁 <b>Gifting Bazaar:</b>\n"
        "• <code>/gift [reply/@user]</code> — Send sweets, crackers & 24k gold coins\n"
        "• <code>/mygifts</code> — View all gifts you received & who sent them 🎁\n"
        "• <code>/shop</code> — Browse available festive gifts and prices\n\n"
        "🎮 <b>Festive Mini-Games:</b>\n"
        "• <code>/phod [amount]</code> — Bet on crackers (2x Win, 3x Jackpot, or Phuss!)\n"
        "• <code>/roll [amount]</code> — Roll 3D Lakshmi animated dice (Roll 4: 1.5x, 5: 2x, 6: 3x!)\n"
        "• <code>/spin [amount]</code> — 3D animated slot machine (777 = 10x Mega Jackpot!)\n"
        "• <code>/dart [amount]</code> — 3D animated dart target shoot (Bullseye = 5x Win!)\n"
        "• <code>/quiz</code> — Ramayana & Diwali trivia (+1,000 coins per win)\n"
        "• <code>/games</code> — Launch the dedicated interactive games arcade\n\n"
        "👥 <b>Group Social Features:</b>\n"
        "• <code>/lifafa &lt;coins&gt; &lt;slots&gt;</code> — Drop red packets in groups\n"
        "• <code>/groupdiya</code> — Community milestone goal (15 Diyas = 3,500 coins drop!)\n"
        "• <i>Every 5 messages in groups triggers random fireworks or coin chests!</i>"
    )

def get_games_help_text() -> str:
    """Detailed guide for mini-games."""
    return (
        "🎮 <b>FESTIVE MINI-GAMES ARCADE MANUAL</b> 🎮\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>1. 🧨 Cracker Burst Game (<code>/phod [amount]</code>):</b>\n"
        "• Bet coins on lighting a firecracker of your choice!\n"
        "• <b>Crackers:</b> Sutli Bomb 💣, Rocket 🚀, Golden Anar 🌋, Phuljhadi 🎇\n"
        "• <b>Chances:</b>\n"
        "  ├ 💥 <b>60% Chance:</b> <b>2x Double Win</b>\n"
        "  ├ 🎆 <b>10% Chance:</b> <b>3x Mega Sky Jackpot</b>\n"
        "  └ 💨 <b>30% Chance:</b> <b>Phusss (Wager lost)</b>\n\n"
        "<b>2. 🎲 Shubh Lakshmi 3D Dice (<code>/roll [amount]</code>):</b>\n"
        "• Auspicious Diwali dice game with physics-animated 3D Telegram dice!\n"
        "• <b>Payouts:</b>\n"
        "  ├ 🎲 <b>Roll 6:</b> 🏆 <b>Triple Shagun (3x Win!)</b>\n"
        "  ├ 🎲 <b>Roll 5:</b> 🎉 <b>Big Win (2x Win!)</b>\n"
        "  ├ 🎲 <b>Roll 4:</b> ✨ <b>Prosperity Win (1.5x Win!)</b>\n"
        "  └ 🎲 <b>Roll 1–3:</b> 💨 House wins\n\n"
        "<b>3. 🎰 Royal 3D Slot Machine (<code>/spin [amount]</code>):</b>\n"
        "• Pull the golden lever on the 3D animated Telegram casino slot machine!\n"
        "• <b>Payouts:</b>\n"
        "  ├ 💎 <b>7 7 7 Alignment:</b> 👑 <b>Royal Mega Jackpot (10x Win!)</b>\n"
        "  ├ 🌟 <b>Triple Match (BARs, Grapes, Lemons):</b> 🎉 <b>Big Win (5x Win!)</b>\n"
        "  ├ ✨ <b>Double Match:</b> ⚡ <b>Double Win (2x Win!)</b>\n"
        "  └ 💨 <b>No Match:</b> Wager lost\n\n"
        "<b>4. 🎯 Shubh Lakshya 3D Darts (<code>/dart [amount]</code>):</b>\n"
        "• Test your festive aim on the physics-animated Telegram dartboard!\n"
        "• <b>Payouts:</b>\n"
        "  ├ 🎯 <b>Center Bullseye (Value 6):</b> 🏆 <b>Grand Bullseye (5x Win!)</b>\n"
        "  ├ 🔴 <b>Inner Ring (Value 4–5):</b> ✨ <b>Target Hit (2x Win!)</b>\n"
        "  ├ ⚪ <b>Outer Ring (Value 2–3):</b> 🪙 <b>Close Shagun (1.2x Win!)</b>\n"
        "  └ 💨 <b>Missed Board (Value 1):</b> Wager lost\n\n"
        "<b>5. 🧠 Diwali Knowledge Quiz (<code>/quiz</code>):</b>\n"
        "• Answer trivia about Ramayana and Deepavali traditions\n"
        "• 🪙 <b>+1,000 Coins</b> for every correct answer!\n"
        "• Cooldown: 5 minutes."
    )

def get_groups_help_text() -> str:
    """Detailed guide for group features."""
    return (
        "👥 <b>GROUP SOCIAL BONDING & MILESTONES</b> 👥\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>1. 🧧 Shubh Lifafa (<code>/lifafa &lt;coins&gt; &lt;slots&gt;</code>):</b>\n"
        "• Drop a lucky shagun envelope in your group chat!\n"
        "• <b>Example:</b> <code>/lifafa 5000 5</code>\n"
        "• 5 members click the button to claim random coin shares!\n"
        "• The player with the highest share is crowned <b>Luckiest King 👑</b>!\n\n"
        "<b>2. 🪔 Community Diya Milestone (<code>/groupdiya</code>):</b>\n"
        "• Every <code>/diya</code> used in the group illuminates the community goal!\n"
        "• Target: <b>15 Diyas</b>.\n"
        "• When reached, a <b>Maha-Deepavali 3,500 Coins Drop</b> spawns for the fastest 3 fingers!\n\n"
        "<b>3. 💥 Automatic Chat Activity Spawns:</b>\n"
        "• Every 5 messages in groups triggers random fireworks bursts or interactive treasure loot drops!"
    )

def get_admin_help_text() -> str:
    """Generate comprehensive control guide for administrators."""
    return (
        "👑 <b>DIWALI BOT — ADMIN CONTROL CENTER</b> 👑\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🛡️ <b>Admin Role Management (Owner Only):</b>\n"
        "• <code>/addadmin &lt;user/@user/reply&gt;</code> — Appoint new admin dynamically\n"
        "• <code>/deladmin &lt;user/@user/reply&gt;</code> — Demote an admin\n"
        "• <code>/admins</code> — List all current Owners & Admins\n\n"
        "🖼️ <b>Dynamic Image Management:</b>\n"
        "• <code>/categories</code> — View all available categories with active image counts\n"
        "• <code>/addimage &lt;category&gt; &lt;url&gt;</code> — Add image URL for command/spawn\n"
        "• <i>(Or reply to any photo with <code>/addimage &lt;category&gt;</code>)</i>\n"
        "• <code>/listimages [category]</code> — List active images and indices\n"
        "• <code>/delimage &lt;category&gt; &lt;index&gt;</code> — Delete image by index\n"
        "• <code>/resetimages [category]</code> — Reset category to config defaults\n"
        "  <i>Categories: diya, diwali, wish, mithai, bomb, fireworks, loot_drop, welcome, daily, loot</i>\n\n"
        "⚡ <b>Force Drop & Spawn Controls:</b>\n"
        "• <code>/fdrop &lt;coins&gt; [slots]</code> — Spawn coin chest in this chat\n"
        "• <code>/fdropall &lt;coins&gt; [slots]</code> — Spawn coin chest in ALL groups\n"
        "• <code>/fdrop_custom coins | slots | btn_text | img_url | message</code> — Full custom drop\n"
        "• <code>/fspawn [diya|bomb|fireworks|cracker]</code> — Force festive burst here\n"
        "• <code>/fspawnall [diya|bomb|fireworks|cracker]</code> — Force festive burst in ALL groups\n\n"
        "⏱️ <b>Dynamic Economy & Cooldowns:</b>\n"
        "• <code>/setlootcooldown &lt;hours&gt;</code> — Change /loot cooldown on the fly\n"
        "• <code>/setlootcoins &lt;coins&gt;</code> — Change /loot reward amount\n"
        "• <code>/setdailycoins &lt;coins&gt;</code> — Change /daily reward amount\n"
        "• <code>/setgroupmin &lt;count&gt;</code> — Change group message threshold (default: 5)\n\n"
        "💰 <b>Admin Coin Controls:</b>\n"
        "• <code>/addcoins &lt;user/@user/reply&gt; &lt;amount&gt;</code> — Mint & grant coins to player\n"
        "• <code>/takecoins &lt;user/@user/reply&gt; &lt;amount&gt;</code> — Deduct coins from player\n"
        "• <code>/setcoins &lt;user/@user/reply&gt; &lt;amount&gt;</code> — Set exact coin balance of player\n\n"
        "📊 <b>User & Bot Information:</b>\n"
        "• <code>/users</code> — Paginated directory of all registered players\n"
        "• <code>/userinfo &lt;user/@user/reply&gt;</code> — Detailed player dossier, balances & inventory\n"
        "• <code>/botinfo</code> — System diagnostics, storage engine & circulation metrics\n"
        "• <code>/groups</code> — List all connected group chats & drop states\n\n"
        "📢 <b>Broadcast & Metrics:</b>\n"
        "• <code>/broadcast &lt;message&gt;</code> — Send announcement to all users & groups\n"
        "• <code>/stats</code> — View live user counts, group counts & database mode"
    )

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with premium festive styling."""
    user = update.effective_user
    chat = update.effective_chat
    if not user:
        return

    # Register user in DB
    user_data = await db.get_user(user.id, {
        "username": user.username,
        "first_name": user.first_name
    })

    if chat.type in ["group", "supergroup"]:
        await db.get_group(chat.id, chat.title)

    bot_me = await context.bot.get_me()
    caption = get_welcome_text(user, user_data.get("coins", 0))
    reply_markup = get_main_menu_keyboard(user.id, bot_me.username)
    img_url = get_random_image("welcome")

    try:
        await update.effective_message.reply_photo(
            photo=img_url,
            caption=caption,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    except Exception:
        await update.effective_message.reply_text(
            text=caption,
            parse_mode="HTML",
            reply_markup=reply_markup
        )

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command with tabbed interactive navigation."""
    user = update.effective_user
    if not user:
        return

    user_is_adm = is_admin(user.id)
    help_text = get_user_help_text()

    keyboard = [
        [
            InlineKeyboardButton("🎮 Mini-Games Manual", callback_data="help_games"),
            InlineKeyboardButton("👥 Group Features Guide", callback_data="help_groups")
        ],
        [
            InlineKeyboardButton("🎁 My Gift Box", callback_data="view_my_gifts"),
            InlineKeyboardButton("🛍️ Gift Bazaar", callback_data="shop_view")
        ],
        [
            InlineKeyboardButton("🎨 UI Theme & Fonts", callback_data="theme_menu"),
            InlineKeyboardButton("🏆 Leaderboards", callback_data="lb_coins")
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="nav_home"),
            InlineKeyboardButton("❌ Close", callback_data="cancel_action")
        ]
    ]

    if user_is_adm:
        keyboard.insert(3, [InlineKeyboardButton("👑 Admin Control Center", callback_data="help_admin")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(help_text, parse_mode="HTML", reply_markup=reply_markup)
