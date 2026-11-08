import random
import asyncio
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
    format_remaining_time
)

# --- 1. LIVE ANIMATED CRACKER BURST (/phod) ---

async def phod_game_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /phod [amount]
    Shows wager selector & cracker choice menu.
    """
    user = update.effective_user
    msg = update.effective_message
    if not user or not msg:
        return

    wager = 500
    if context.args and context.args[0].isdigit():
        wager = int(context.args[0])

    if wager < 100:
        await msg.reply_text("❌ Minimum wager for /phod is <b>100</b> coins!", parse_mode="HTML")
        return
    if wager > 50000:
        await msg.reply_text("❌ Maximum wager for /phod is <b>50,000</b> coins!", parse_mode="HTML")
        return

    user_data = await db.get_user(user.id, {"username": user.username, "first_name": user.first_name})
    coins = user_data.get("coins", 0)

    if coins < wager:
        await msg.reply_text(
            f"❌ <b>Insufficient Coins!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"You need <code>{format_number(wager)}</code> coins to play, but have <code>{format_number(coins)}</code> coins.\n"
            f"Claim free coins with /daily or /loot! 🪙",
            parse_mode="HTML"
        )
        return

    menu_text = (
        f"🧨 <b>CRACKER BURST — LIVE SUSPENSE ARENA</b> 🧨\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Player:</b> {get_mention(user)}\n"
        f"🪙 <b>Selected Wager:</b> <code>{format_number(wager)}</code> Coins\n\n"
        f"<i>Select which firecracker you want to ignite:</i>\n\n"
        f"• 💣 <b>Sutli Bomb</b> — <i>High blast thrill (2x to 3x)</i>\n"
        f"• 🚀 <b>Sky Rocket</b> — <i>High altitude jackpot potential</i>\n"
        f"• 🌋 <b>Golden Anar</b> — <i>Spectacular golden fountain</i>\n"
        f"• 🎇 <b>Electric Phuljhadi</b> — <i>Lucky sparkle flame</i>\n\n"
        f"⚡ <i>Tap below to light the fuse and watch the live blast!</i>"
    )

    keyboard = [
        [
            InlineKeyboardButton("💣 Sutli Bomb", callback_data=f"phod_live:{wager}:bomb"),
            InlineKeyboardButton("🚀 Sky Rocket", callback_data=f"phod_live:{wager}:rocket")
        ],
        [
            InlineKeyboardButton("🌋 Golden Anar", callback_data=f"phod_live:{wager}:anar"),
            InlineKeyboardButton("🎇 Electric Sparkler", callback_data=f"phod_live:{wager}:sparkler")
        ],
        [
            InlineKeyboardButton("🪙 Bet 500", callback_data="phod_setwager:500"),
            InlineKeyboardButton("🪙 Bet 1,000", callback_data="phod_setwager:1000"),
            InlineKeyboardButton("🪙 Bet 5,000", callback_data="phod_setwager:5000")
        ],
        [InlineKeyboardButton("🔙 Back to Games", callback_data="help_games")]
    ]

    await msg.reply_text(menu_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def phod_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process live multi-frame animated cracker sequence."""
    query = update.callback_query
    if not query or not query.data:
        return

    data = query.data
    user = query.from_user

    # Handle quick wager buttons
    if data.startswith("phod_setwager:"):
        await query.answer()
        wager = int(data.split(":")[1])
        context.args = [str(wager)]
        await phod_game_handler(update, context)
        return

    if not data.startswith("phod_live:"):
        return

    parts = data.split(":")
    if len(parts) != 3:
        return

    wager = int(parts[1])
    cracker_type = parts[2]

    # Verify balance
    user_data = await db.get_user(user.id)
    if user_data.get("coins", 0) < wager:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return

    # Deduct wager
    await db.deduct_coins(user.id, wager)
    await query.answer("🕯️ Sparking the match...")

    cracker_names = {
        "bomb": ("Sutli Bomb", "💣"),
        "rocket": ("Sky Rocket", "🚀"),
        "anar": ("Golden Anar", "🌋"),
        "sparkler": ("Electric Sparkler", "🎇")
    }
    c_name, c_icon = cracker_names.get(cracker_type, ("Firecracker", "🧨"))
    mention = get_mention(user)

    # FRAME 1: Lighting fuse
    frame1 = (
        f"{c_icon} <b>IGNITING {c_name.upper()}...</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Player:</b> {mention} | 🪙 <b>Wager:</b> <code>{format_number(wager)}</code>\n\n"
        f"🕯️ Touching the match to the fuse...\n\n"
        f"<code>[🔥───────────{c_icon}]</code>\n"
        f"<i>*Tssssssssssssssssssssssssss...*</i>"
    )
    try:
        await query.edit_message_text(frame1, parse_mode="HTML")
    except Exception:
        pass

    await asyncio.sleep(1.2)

    # FRAME 2: Spark traveling down fuse (Live animation!)
    frame2 = (
        f"{c_icon} <b>FUSE IS BURNING FAST!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Player:</b> {mention} | 🪙 <b>Wager:</b> <code>{format_number(wager)}</code>\n\n"
        f"⚡ Spark running down the cord! Take cover!\n\n"
        f"<code>[═════⚡─────{c_icon}]</code>\n"
        f"<i>*SSSSSSSSSSSHHHHHHH... CRACKLE!*</i> 💨"
    )
    try:
        await query.edit_message_text(frame2, parse_mode="HTML")
    except Exception:
        pass

    await asyncio.sleep(1.2)

    # FRAME 3: Climax suspense
    frame3 = (
        f"{c_icon} <b>DETONATION IMMINENT!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Player:</b> {mention} | 🪙 <b>Wager:</b> <code>{format_number(wager)}</code>\n\n"
        f"💨 Smoke swirling violently around {c_name}!\n\n"
        f"<code>[═══════════💥{c_icon}]</code>\n"
        f"<i>*3... 2... 1...*</i>"
    )
    try:
        await query.edit_message_text(frame3, parse_mode="HTML")
    except Exception:
        pass

    await asyncio.sleep(1.1)

    # Random outcome
    # 0.00 - 0.60: Win 2x
    # 0.60 - 0.70: Jackpot 3x
    # 0.70 - 1.00: Phuss (Loss)
    roll = random.random()

    if roll < 0.60:
        # 2x Win
        profit = wager * 2
        new_bal = await db.add_coins(user.id, profit)
        result_text = (
            f"💥💥 <b>B O O O M !  D H A M A K A ! (2X)</b> 💥💥\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Player:</b> {mention}\n"
            f"🧨 <b>Cracker:</b> {c_icon} <b>{c_name}</b>\n\n"
            f"✨ <i>Glorious golden sparks shower the night sky in high decibels!</i>\n\n"
            f"🏆 <b>RESULT:</b> <b>SPECTACULAR VICTORY (2x)!</b>\n"
            f"🪙 <b>Prize Won:</b> +<code>{format_number(profit)}</code> Coins (+{format_number(wager)} profit)\n"
            f"💰 <b>Total Balance:</b> <code>{format_number(new_bal)}</code> Coins"
        )
    elif roll < 0.70:
        # 3x Jackpot
        profit = wager * 3
        new_bal = await db.add_coins(user.id, profit)
        result_text = (
            f"🎆🌟 <b>M E G A  S K Y  J A C K P O T ! (3X)</b> 🌟🎆\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Player:</b> {mention}\n"
            f"🧨 <b>Cracker:</b> {c_icon} <b>{c_name}</b>\n\n"
            f"🌟 <i>UNBELIEVABLE! Multi-tiered peony fireballs explode across Ayodhya!</i>\n\n"
            f"👑 <b>RESULT:</b> <b>ROYAL SUPER JACKPOT (3x)!</b>\n"
            f"🪙 <b>Prize Won:</b> +<code>{format_number(profit)}</code> Coins (+{format_number(profit - wager)} profit)\n"
            f"💰 <b>Total Balance:</b> <code>{format_number(new_bal)}</code> Coins"
        )
    else:
        # Loss: Phusss
        user_bal = (await db.get_user(user.id)).get("coins", 0)
        phuss_lines = [
            "Fhhuusssss... baati bujh gayi aur sirf dhuan nikla! 💨",
            "Moisture in the air extinguished the fuse! Phussss! 🌧️",
            "Khota patakha nikal gaya! 💨 Better luck next time!"
        ]
        chosen_line = random.choice(phuss_lines)
        result_text = (
            f"💨 <b>P H U S S S S S S S !  O H  N O !</b> 💨\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Player:</b> {mention}\n"
            f"🧨 <b>Cracker:</b> {c_icon} <b>{c_name}</b>\n\n"
            f"<i>\"{chosen_line}\"</i>\n\n"
            f"❌ <b>RESULT:</b> Lost <code>{format_number(wager)}</code> Coins.\n"
            f"💰 <b>Remaining Balance:</b> <code>{format_number(user_bal)}</code> Coins\n\n"
            f"<i>Goddess Lakshmi favors the persistent! Try another one!</i> 🪔"
        )

    keyboard = [
        [
            InlineKeyboardButton(f"🔁 Play Again ({format_number(wager)} 🪙)", callback_data=f"phod_live:{wager}:{cracker_type}"),
            InlineKeyboardButton("🎲 Roll Dice", callback_data="game_start_roll")
        ],
        [
            InlineKeyboardButton("🎮 All Games", callback_data="help_games"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="nav_home")
        ]
    ]

    try:
        await query.edit_message_text(result_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await query.message.reply_text(result_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# --- 2. 3D ANIMATED SHUBH LAKSHMI DICE (/roll) ---

async def roll_game_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /roll [amount] or /dice [amount]
    Auspicious Diwali dice rolling with Telegram's animated 3D physics dice!
    """
    user = update.effective_user
    msg = update.effective_message
    if not user or not msg:
        return

    wager = 500
    if context.args and context.args[0].isdigit():
        wager = int(context.args[0])

    if wager < 100:
        await msg.reply_text("❌ Minimum wager for /roll is <b>100</b> coins!", parse_mode="HTML")
        return
    if wager > 50000:
        await msg.reply_text("❌ Maximum wager for /roll is <b>50,000</b> coins!", parse_mode="HTML")
        return

    user_data = await db.get_user(user.id, {"username": user.username, "first_name": user.first_name})
    current_coins = user_data.get("coins", 0)

    if current_coins < wager:
        await msg.reply_text(
            f"❌ <b>Insufficient Coins!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"You need <code>{format_number(wager)}</code> coins to roll the sacred dice.\n"
            f"Current Balance: <code>{format_number(current_coins)}</code> Coins.",
            parse_mode="HTML"
        )
        return

    # Deduct wager upfront
    await db.deduct_coins(user.id, wager)
    mention = get_mention(user)

    intro_msg = await msg.reply_text(
        f"🎲 <b>SACRED LAKSHMI 3D DICE ROLL</b> 🎲\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Player:</b> {mention} | 🪙 <b>Wager:</b> <code>{format_number(wager)}</code> Coins\n\n"
        f"<i>Tossing the 3D gilded ivory dice onto the velvet festival table...</i> ✨",
        parse_mode="HTML"
    )

    # Send native 3D animated Telegram dice
    dice_msg = await msg.reply_dice(emoji="🎲")
    dice_value = dice_msg.dice.value

    # Wait for Telegram's rolling animation
    await asyncio.sleep(3.2)

    if dice_value == 6:
        payout = wager * 3
        new_bal = await db.add_coins(user.id, payout)
        result_text = (
            f"🏆🌟 <b>ROLLED A 6! TRIPLE SHAGUN JACKPOT! (3X)</b> 🌟🏆\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Player:</b> {mention}\n"
            f"🎲 <b>Dice Value:</b> <b>6 [ ⚅ ]</b>\n\n"
            f"Auspicious omen! Goddess Lakshmi blesses your roll with pure prosperity!\n\n"
            f"🪙 <b>Prize Won:</b> +<code>{format_number(payout)}</code> Coins (+{format_number(payout - wager)} profit)\n"
            f"💰 <b>New Balance:</b> <code>{format_number(new_bal)}</code> Coins"
        )
    elif dice_value == 5:
        payout = wager * 2
        new_bal = await db.add_coins(user.id, payout)
        result_text = (
            f"🎉 <b>ROLLED A 5! BIG DOUBLE WIN! (2X)</b> 🎉\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Player:</b> {mention}\n"
            f"🎲 <b>Dice Value:</b> <b>5 [ ⚄ ]</b>\n\n"
            f"Superb roll! You successfully doubled your shagun!\n\n"
            f"🪙 <b>Prize Won:</b> +<code>{format_number(payout)}</code> Coins (+{format_number(wager)} profit)\n"
            f"💰 <b>New Balance:</b> <code>{format_number(new_bal)}</code> Coins"
        )
    elif dice_value == 4:
        payout = int(wager * 1.5)
        new_bal = await db.add_coins(user.id, payout)
        result_text = (
            f"✨ <b>ROLLED A 4! PROSPERITY WIN! (1.5X)</b> ✨\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Player:</b> {mention}\n"
            f"🎲 <b>Dice Value:</b> <b>4 [ ⚃ ]</b>\n\n"
            f"Favorable roll! A sweet festive return on your coins!\n\n"
            f"🪙 <b>Prize Won:</b> +<code>{format_number(payout)}</code> Coins (+{format_number(payout - wager)} profit)\n"
            f"💰 <b>New Balance:</b> <code>{format_number(new_bal)}</code> Coins"
        )
    else:
        user_bal = (await db.get_user(user.id)).get("coins", 0)
        remarks = {
            1: "Rolled a 1 [ ⚀ ]! Kismat ne thoda chakma diya! 💨",
            2: "Rolled a 2 [ ⚁ ]! Agli baar Lakshmi Mata ka aashirwad zaroor milega! 🕯️",
            3: "Rolled a 3 [ ⚂ ]! Bas thode se reh gaye! 🎲"
        }
        result_text = (
            f"💨 <b>ROLLED A {dice_value}! HARD LUCK!</b> 💨\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Player:</b> {mention}\n"
            f"🎲 <b>Dice Value:</b> <b>{dice_value}</b>\n\n"
            f"<i>\"{remarks.get(dice_value, 'Better luck next roll!')}\"</i>\n\n"
            f"❌ <b>Lost:</b> <code>{format_number(wager)}</code> Coins\n"
            f"💰 <b>Current Balance:</b> <code>{format_number(user_bal)}</code> Coins"
        )

    keyboard = [
        [
            InlineKeyboardButton(f"🔁 Roll Again ({format_number(wager)} 🪙)", callback_data="game_start_roll"),
            InlineKeyboardButton("🎰 Spin Slot Machine", callback_data="game_start_spin")
        ],
        [
            InlineKeyboardButton("🎮 All Games", callback_data="help_games"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="nav_home")
        ]
    ]

    await dice_msg.reply_text(result_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# --- 3. LIVE 3D ANIMATED SLOT MACHINE (/spin or /slot) ---

async def slot_game_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /spin or /slot [amount]
    Spins the 3D animated native Telegram Slot Machine reels!
    Values (1-64):
    • 64: 777 TRIPLE SEVEN ROYAL JACKPOT! (10x Win!)
    • 43, 22, 1: Triple BAR / Fruit (5x Win!)
    • Minor combinations: 1.5x - 2x
    """
    user = update.effective_user
    msg = update.effective_message
    if not user or not msg:
        return

    wager = 500
    if context.args and context.args[0].isdigit():
        wager = int(context.args[0])

    if wager < 100:
        await msg.reply_text("❌ Minimum wager for /spin is <b>100</b> coins!", parse_mode="HTML")
        return
    if wager > 50000:
        await msg.reply_text("❌ Maximum wager for /spin is <b>50,000</b> coins!", parse_mode="HTML")
        return

    user_data = await db.get_user(user.id, {"username": user.username, "first_name": user.first_name})
    if user_data.get("coins", 0) < wager:
        await msg.reply_text(f"❌ Insufficient balance! You need <code>{format_number(wager)}</code> coins to spin.", parse_mode="HTML")
        return

    await db.deduct_coins(user.id, wager)
    mention = get_mention(user)

    await msg.reply_text(
        f"🎰 <b>ROYAL DIWALI 3D SLOT MACHINE</b> 🎰\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Player:</b> {mention} | 🪙 <b>Wager:</b> <code>{format_number(wager)}</code> Coins\n\n"
        f"<i>Pulling the golden lever! Watch the 3D reels spin...</i> ⚡",
        parse_mode="HTML"
    )

    # Send native 3D animated Slot Machine
    slot_msg = await msg.reply_dice(emoji="🎰")
    val = slot_msg.dice.value

    # Wait for reel animation (~3.2s)
    await asyncio.sleep(3.3)

    # Telegram Slot Machine values:
    # 64: '777' (Jackpot!)
    # 43: 'BAR BAR BAR'
    # 22: 'Grape Grape Grape'
    # 1: 'Lemon Lemon Lemon'
    # If val in [16, 32, 48]: Two 7s or good partial matches
    if val == 64:
        payout = wager * 10
        new_bal = await db.add_coins(user.id, payout)
        res_text = (
            f"👑💎 <b>7 7 7 !  ROYAL MEGA JACKPOT! (10X)</b> 💎👑\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Player:</b> {mention}\n"
            f"🎰 <b>Reels:</b> <b>[ 7 | 7 | 7 ]</b>\n\n"
            f"UNBELIEVABLE! All three lucky sevens aligned on the golden payline!\n\n"
            f"🪙 <b>Prize Won:</b> +<code>{format_number(payout)}</code> Coins (+{format_number(payout - wager)} profit)\n"
            f"💰 <b>New Balance:</b> <code>{format_number(new_bal)}</code> Coins"
        )
    elif val in [43, 22, 1]:
        payout = wager * 5
        new_bal = await db.add_coins(user.id, payout)
        res_text = (
            f"🌟🎉 <b>TRIPLE MATCH DELIGHT! (5X)</b> 🎉🌟\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Player:</b> {mention}\n"
            f"🎰 <b>Reels:</b> <b>Triple Match!</b>\n\n"
            f"Huge hit! Three matching festive symbols on the payline!\n\n"
            f"🪙 <b>Prize Won:</b> +<code>{format_number(payout)}</code> Coins (+{format_number(payout - wager)} profit)\n"
            f"💰 <b>New Balance:</b> <code>{format_number(new_bal)}</code> Coins"
        )
    elif val in [16, 32, 48]:
        payout = wager * 2
        new_bal = await db.add_coins(user.id, payout)
        res_text = (
            f"✨ <b>DOUBLE MATCH WIN! (2X)</b> ✨\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Player:</b> {mention}\n"
            f"🎰 <b>Reels:</b> <b>Double Match!</b>\n\n"
            f"Two matching symbols! You doubled your coins!\n\n"
            f"🪙 <b>Prize Won:</b> +<code>{format_number(payout)}</code> Coins (+{format_number(wager)} profit)\n"
            f"💰 <b>New Balance:</b> <code>{format_number(new_bal)}</code> Coins"
        )
    else:
        user_bal = (await db.get_user(user.id)).get("coins", 0)
        res_text = (
            f"💨 <b>SPIN COMPLETE! NO MATCH!</b> 💨\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Player:</b> {mention}\n\n"
            f"<i>Reels didn't line up this time! Pull the lever again!</i>\n\n"
            f"❌ <b>Lost:</b> <code>{format_number(wager)}</code> Coins\n"
            f"💰 <b>Current Balance:</b> <code>{format_number(user_bal)}</code> Coins"
        )

    keyboard = [
        [
            InlineKeyboardButton(f"🎰 Spin Again ({format_number(wager)} 🪙)", callback_data="game_start_spin"),
            InlineKeyboardButton("🎯 Play Darts", callback_data="game_start_dart")
        ],
        [
            InlineKeyboardButton("🎮 All Games", callback_data="help_games"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="nav_home")
        ]
    ]
    await slot_msg.reply_text(res_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# --- 4. LIVE 3D ANIMATED DART TARGET SHOOT (/dart) ---

async def dart_game_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /dart [amount]
    Throws an animated 3D Telegram Dart at the Diwali bullseye!
    Values:
    • 6: 🎯 BULLSEYE! (5x Win!)
    • 5, 4: Inner Ring (2x Win!)
    • 2, 3: Outer Ring (1.2x Win!)
    • 1: Missed Board (0x)
    """
    user = update.effective_user
    msg = update.effective_message
    if not user or not msg:
        return

    wager = 500
    if context.args and context.args[0].isdigit():
        wager = int(context.args[0])

    if wager < 100:
        await msg.reply_text("❌ Minimum wager for /dart is <b>100</b> coins!", parse_mode="HTML")
        return
    if wager > 50000:
        await msg.reply_text("❌ Maximum wager for /dart is <b>50,000</b> coins!", parse_mode="HTML")
        return

    user_data = await db.get_user(user.id, {"username": user.username, "first_name": user.first_name})
    if user_data.get("coins", 0) < wager:
        await msg.reply_text(f"❌ Insufficient balance! You need <code>{format_number(wager)}</code> coins to play.", parse_mode="HTML")
        return

    await db.deduct_coins(user.id, wager)
    mention = get_mention(user)

    await msg.reply_text(
        f"🎯 <b>DIWALI 3D BULLSEYE DART SHOOT</b> 🎯\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Archer:</b> {mention} | 🪙 <b>Wager:</b> <code>{format_number(wager)}</code> Coins\n\n"
        f"<i>Taking careful aim at the golden festival target...</i> 🏹",
        parse_mode="HTML"
    )

    # Send 3D animated Dart
    dart_msg = await msg.reply_dice(emoji="🎯")
    val = dart_msg.dice.value

    # Wait for flight animation
    await asyncio.sleep(2.8)

    if val == 6:
        payout = wager * 5
        new_bal = await db.add_coins(user.id, payout)
        res_text = (
            f"🎯🌟 <b>PERFECT BULLSEYE! (5X JACKPOT!)</b> 🌟🎯\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Archer:</b> {mention}\n"
            f"🎯 <b>Hit:</b> <b>DEAD CENTER BULLSEYE! (6/6)</b>\n\n"
            f"Flawless precision! Lord Rama's supreme archery blessing!\n\n"
            f"🪙 <b>Prize Won:</b> +<code>{format_number(payout)}</code> Coins (+{format_number(payout - wager)} profit)\n"
            f"💰 <b>New Balance:</b> <code>{format_number(new_bal)}</code> Coins"
        )
    elif val in [4, 5]:
        payout = wager * 2
        new_bal = await db.add_coins(user.id, payout)
        res_text = (
            f"🎉 <b>INNER RED RING HIT! (2X)</b> 🎉\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Archer:</b> {mention}\n"
            f"🎯 <b>Hit:</b> <b>Inner Target Ring ({val}/6)</b>\n\n"
            f"Excellent throw! Clean double return!\n\n"
            f"🪙 <b>Prize Won:</b> +<code>{format_number(payout)}</code> Coins (+{format_number(wager)} profit)\n"
            f"💰 <b>New Balance:</b> <code>{format_number(new_bal)}</code> Coins"
        )
    elif val in [2, 3]:
        payout = int(wager * 1.2)
        new_bal = await db.add_coins(user.id, payout)
        res_text = (
            f"✨ <b>OUTER RING GRAZE! (1.2X)</b> ✨\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Archer:</b> {mention}\n"
            f"🎯 <b>Hit:</b> <b>Outer Target ({val}/6)</b>\n\n"
            f"On the board! Small festive profit!\n\n"
            f"🪙 <b>Prize Won:</b> +<code>{format_number(payout)}</code> Coins (+{format_number(payout - wager)} profit)\n"
            f"💰 <b>New Balance:</b> <code>{format_number(new_bal)}</code> Coins"
        )
    else:
        user_bal = (await db.get_user(user.id)).get("coins", 0)
        res_text = (
            f"💨 <b>MISSED THE BOARD! (1/6)</b> 💨\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Archer:</b> {mention}\n\n"
            f"<i>The dart went wide into the curtain! Aim again!</i>\n\n"
            f"❌ <b>Lost:</b> <code>{format_number(wager)}</code> Coins\n"
            f"💰 <b>Current Balance:</b> <code>{format_number(user_bal)}</code> Coins"
        )

    keyboard = [
        [
            InlineKeyboardButton(f"🎯 Throw Again ({format_number(wager)} 🪙)", callback_data="game_start_dart"),
            InlineKeyboardButton("🧨 Play /phod", callback_data="game_start_phod")
        ],
        [
            InlineKeyboardButton("🎮 All Games", callback_data="help_games"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="nav_home")
        ]
    ]
    await dart_msg.reply_text(res_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# --- 5. DEDICATED /games COMMAND HUB ---

async def games_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /games or /game command with modern, visual arcade UI.
    """
    user = update.effective_user
    msg = update.effective_message
    if not user or not msg:
        return

    user_data = await db.get_user(user.id, {"username": user.username, "first_name": user.first_name})
    coins = user_data.get("coins", 0)

    games_text = (
        "🎮 <b>DIWALI LIVE 3D FESTIVE ARCADE</b> 🎮\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Player:</b> {get_mention(user)}\n"
        f"🪙 <b>Available Balance:</b> <code>{format_number(coins)}</code> Coins\n\n"
        "<i>All games feature live 3D physics animations & real-time suspense!</i>\n\n"
        "🧨 <b>1. Cracker Burst Live (<code>/phod [amount]</code>)</b>\n"
        "• Live burning fuse animation & explosive reveals (2x Win to 3x Jackpot)\n\n"
        "🎲 <b>2. Sacred Lakshmi 3D Dice (<code>/roll [amount]</code>)</b>\n"
        "• Native physics-animated 3D dice (Roll 6: 3x Jackpot, 5: 2x, 4: 1.5x)\n\n"
        "🎰 <b>3. Royal 3D Slot Machine (<code>/spin [amount]</code>)</b>\n"
        "• 3D animated spinning slot reels (Triple 7s pays <b>10x ROYAL JACKPOT</b>!)\n\n"
        "🎯 <b>4. Diwali Bullseye Darts (<code>/dart [amount]</code>)</b>\n"
        "• 3D animated flight to the board (Center Bullseye pays <b>5x Win</b>!)\n\n"
        "🧠 <b>5. Diwali Trivia Quiz (<code>/quiz</code>)</b>\n"
        "• 4-option Ramayana trivia (Win <b>+1,000 Coins</b> every 5 mins)\n\n"
        "🧧 <b>6. Shubh Lifafa Packets (<code>/lifafa &lt;coins&gt; &lt;slots&gt;</code>)</b>\n"
        "• Drop festive red packets in group chats for friends to claim!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Tap any game below to launch live:</i>"
    )

    keyboard = [
        [
            InlineKeyboardButton("🧨 Live /phod", callback_data="game_start_phod"),
            InlineKeyboardButton("🎲 3D Dice /roll", callback_data="game_start_roll")
        ],
        [
            InlineKeyboardButton("🎰 3D Slot /spin", callback_data="game_start_spin"),
            InlineKeyboardButton("🎯 3D Darts /dart", callback_data="game_start_dart")
        ],
        [
            InlineKeyboardButton("🧠 Diwali Quiz", callback_data="game_start_quiz"),
            InlineKeyboardButton("🎒 My Profile", callback_data="view_profile_quick")
        ],
        [
            InlineKeyboardButton("🎁 Gift Bazaar", callback_data="shop_view"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="nav_home")
        ]
    ]

    await msg.reply_text(games_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
