from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from handlers.economy import render_leaderboard
from handlers.festive import diya_handler
from handlers.gift import gift_command_handler
from utils import is_admin

async def general_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle navigation and general interactive buttons."""
    query = update.callback_query
    if not query or not query.data:
        return

    data = query.data
    user = query.from_user

    if data == "nav_home":
        await query.answer()
        from handlers.start import get_welcome_text, get_main_menu_keyboard
        from database import db
        user_data = await db.get_user(user.id)
        bot_me = await context.bot.get_me()
        welcome_text = get_welcome_text(user, user_data.get("coins", 0))
        markup = get_main_menu_keyboard(user.id, bot_me.username)
        try:
            await query.edit_message_text(welcome_text, parse_mode="HTML", reply_markup=markup)
        except Exception:
            try:
                await query.edit_message_caption(caption=welcome_text, parse_mode="HTML", reply_markup=markup)
            except Exception:
                await query.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=markup)

    elif data in ["help_menu", "help_user"]:
        await query.answer()
        from handlers.start import get_user_help_text
        help_text = get_user_help_text()

        keyboard = [
            [
                InlineKeyboardButton("🎮 Mini-Games Guide", callback_data="help_games"),
                InlineKeyboardButton("👥 Group Features Guide", callback_data="help_groups")
            ],
            [
                InlineKeyboardButton("🎁 My Gifts Box", callback_data="view_my_gifts"),
                InlineKeyboardButton("🛍️ Gift Bazaar", callback_data="shop_view")
            ],
            [
                InlineKeyboardButton("🎨 UI Theme & Fonts", callback_data="theme_menu"),
                InlineKeyboardButton("🏆 Leaderboards", callback_data="lb_coins")
            ]
        ]
        if is_admin(user.id):
            keyboard.append([InlineKeyboardButton("👑 Admin Controls", callback_data="help_admin")])
        keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="nav_home")])

        try:
            await query.edit_message_text(help_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            await query.message.reply_text(help_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "help_games":
        await query.answer()
        from handlers.start import get_games_help_text
        games_text = get_games_help_text()

        keyboard = [
            [InlineKeyboardButton("🔙 Back to Commands", callback_data="help_user")],
            [InlineKeyboardButton("👥 Group Features", callback_data="help_groups")]
        ]
        try:
            await query.edit_message_text(games_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            await query.message.reply_text(games_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "help_groups":
        await query.answer()
        from handlers.start import get_groups_help_text
        groups_text = get_groups_help_text()

        keyboard = [
            [InlineKeyboardButton("🔙 Back to Commands", callback_data="help_user")],
            [InlineKeyboardButton("🎮 Mini-Games Guide", callback_data="help_games")]
        ]
        try:
            await query.edit_message_text(groups_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            await query.message.reply_text(groups_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "help_admin":
        if not is_admin(user.id):
            await query.answer("⛔ Access Denied: You are not an administrator.", show_alert=True)
            return

        await query.answer()
        from handlers.start import get_admin_help_text
        admin_text = get_admin_help_text()

        keyboard = [
            [
                InlineKeyboardButton("👤 User Commands", callback_data="help_user"),
                InlineKeyboardButton("🖼️ Image Categories", callback_data="view_cats_info")
            ],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="nav_home")]
        ]
        try:
            await query.edit_message_text(admin_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            await query.message.reply_text(admin_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data in ["view_cats_info", "admin_view_cats"]:
        if not is_admin(user.id):
            await query.answer("⛔ Access Denied: Administrator privileges required.", show_alert=True)
            return
        await query.answer()
        from handlers.admin import generate_categories_overview
        text, markup = await generate_categories_overview()
        try:
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
        except Exception:
            await query.message.reply_text(text, parse_mode="HTML", reply_markup=markup)

    elif data.startswith("cat_inspect:"):
        if not is_admin(user.id):
            await query.answer("⛔ Access Denied: Administrator privileges required.", show_alert=True)
            return
        await query.answer()
        cat = data.split(":", 1)[1]
        from handlers.admin import generate_category_detail
        text, markup = await generate_category_detail(cat)
        try:
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
        except Exception:
            await query.message.reply_text(text, parse_mode="HTML", reply_markup=markup)

    elif data == "trigger_diya":
        await query.answer()
        await diya_handler(update, context)

    elif data == "game_start_phod":
        await query.answer()
        from handlers.minigame import phod_game_handler
        context.args = ["500"]
        await phod_game_handler(update, context)

    elif data == "game_start_roll":
        await query.answer()
        from handlers.minigame import roll_game_handler
        context.args = ["500"]
        await roll_game_handler(update, context)

    elif data == "game_start_spin":
        await query.answer()
        from handlers.minigame import slot_game_handler
        context.args = ["500"]
        await slot_game_handler(update, context)

    elif data == "game_start_dart":
        await query.answer()
        from handlers.minigame import dart_game_handler
        context.args = ["500"]
        await dart_game_handler(update, context)

    elif data == "game_start_quiz":
        await query.answer()
        from handlers.quiz import quiz_handler
        await quiz_handler(update, context)

    elif data == "view_profile_quick":
        await query.answer()
        from handlers.economy import profile_handler
        await profile_handler(update, context)

    elif data == "view_my_gifts":
        await query.answer()
        from handlers.gift import generate_my_gifts_view
        text, markup = await generate_my_gifts_view(user.id)
        try:
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup, disable_web_page_preview=True)
        except Exception:
            await query.message.reply_text(text, parse_mode="HTML", reply_markup=markup, disable_web_page_preview=True)

    elif data == "theme_menu":
        await query.answer()
        from handlers.theme import theme_command_handler
        await theme_command_handler(update, context)

    elif data == "help_gift":
        await query.answer()
        await gift_command_handler(update, context)

    elif data in ["lb_coins", "lb_gifts_sent", "lb_wishes_sent"]:
        await query.answer()
        sort_by = data.replace("lb_", "")
        await render_leaderboard(update, context, sort_by=sort_by)

    elif data.startswith("users_page:"):
        if not is_admin(user.id):
            await query.answer("⛔ Access Denied: Administrator privileges required.", show_alert=True)
            return
        await query.answer()
        from handlers.admin import generate_users_directory
        try:
            page = int(data.split(":")[1])
        except (ValueError, IndexError):
            page = 1
        text, markup = await generate_users_directory(page=page)
        try:
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup, disable_web_page_preview=True)
        except Exception:
            await query.message.reply_text(text, parse_mode="HTML", reply_markup=markup, disable_web_page_preview=True)

    elif data.startswith("groups_page:"):
        if not is_admin(user.id):
            await query.answer("⛔ Access Denied: Administrator privileges required.", show_alert=True)
            return
        await query.answer()
        from handlers.admin import generate_groups_directory
        try:
            page = int(data.split(":")[1])
        except (ValueError, IndexError):
            page = 1
        text, markup = await generate_groups_directory(page=page)
        try:
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
        except Exception:
            await query.message.reply_text(text, parse_mode="HTML", reply_markup=markup)

    elif data == "admin_botinfo":
        if not is_admin(user.id):
            await query.answer("⛔ Access Denied: Administrator privileges required.", show_alert=True)
            return
        await query.answer()
        from handlers.admin import get_bot_info_text
        text, markup = await get_bot_info_text(context)
        try:
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
        except Exception:
            await query.message.reply_text(text, parse_mode="HTML", reply_markup=markup)
