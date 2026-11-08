from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import db
from utils import (
    get_mention,
    to_font,
    get_theme,
    format_banner,
    THEMES,
    DEFAULT_THEME,
    is_admin
)

async def theme_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /theme or /font command.
    Allows user to select their dynamic UI typography & decorative frame style.
    """
    user = update.effective_user
    msg = update.effective_message
    if not user or not msg:
        return

    user_data = await db.get_user(user.id)
    current_theme_id = user_data.get("theme", DEFAULT_THEME)

    text = render_theme_menu_text(user, current_theme_id)
    reply_markup = get_theme_keyboard(current_theme_id)

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)
        except Exception:
            await update.callback_query.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)
    else:
        await msg.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)

def render_theme_menu_text(user, active_theme_id: str) -> str:
    """Render dynamic theme selection preview card."""
    thm = get_theme(active_theme_id)
    banner = format_banner("Aesthetic Theme Studio", active_theme_id, "Customize your fonts & frames")

    preview_lines = [
        banner,
        f"👤 <b>Player:</b> {get_mention(user)}",
        f"🎨 <b>Current Theme:</b> <b>{thm['name']}</b>\n",
        "<i>Select any theme below to change your font & decorative look:</i>\n"
    ]

    for t_id, t in THEMES.items():
        is_active = " (Active ✅)" if t_id == active_theme_id else ""
        sample_text = to_font("Diwali Shagun 2026", t["font_style"])
        preview_lines.append(f"• <b>{t['name']}</b>{is_active}\n  Font Preview: <code>{sample_text}</code>\n  Border: <code>{t['top_border']}</code>\n")

    preview_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
    preview_lines.append("<i>All bot messages, profiles & game outputs will render in your chosen style!</i>")
    return "\n".join(preview_lines)

def get_theme_keyboard(active_theme_id: str) -> InlineKeyboardMarkup:
    """Buttons for selecting themes."""
    buttons = []
    for t_id, t in THEMES.items():
        mark = "✅ " if t_id == active_theme_id else ""
        buttons.append([InlineKeyboardButton(f"{mark}{t['name']}", callback_data=f"set_theme_user:{t_id}")])

    buttons.append([
        InlineKeyboardButton("🎒 My Profile", callback_data="view_profile_quick"),
        InlineKeyboardButton("🏠 Main Menu", callback_data="nav_home")
    ])
    return InlineKeyboardMarkup(buttons)

async def theme_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process user theme selection in-place."""
    query = update.callback_query
    if not query or not query.data or not query.data.startswith("set_theme_user:"):
        return

    theme_id = query.data.split(":", 1)[1]
    user = query.from_user

    if theme_id not in THEMES:
        await query.answer("Invalid theme selected!", show_alert=True)
        return

    await db.update_user(user.id, {"theme": theme_id})
    await query.answer(f"🎨 Theme updated to {THEMES[theme_id]['name']}!", show_alert=True)

    # Re-render in the new theme!
    text = render_theme_menu_text(user, theme_id)
    reply_markup = get_theme_keyboard(theme_id)

    try:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)
    except Exception:
        pass

async def admin_set_theme_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settheme <theme_id> (Admin only)."""
    user = update.effective_user
    msg = update.effective_message
    if not user or not msg or not is_admin(user.id):
        return

    if not context.args:
        valid_ids = ", ".join(THEMES.keys())
        await msg.reply_text(f"Usage: <code>/settheme &lt;theme_id&gt;</code>\nValid options: <code>{valid_ids}</code>", parse_mode="HTML")
        return

    chosen = context.args[0].lower()
    if chosen not in THEMES:
        valid_ids = ", ".join(THEMES.keys())
        await msg.reply_text(f"❌ Invalid theme ID. Choose from: <code>{valid_ids}</code>", parse_mode="HTML")
        return

    await db.set_setting("default_theme", chosen)
    await msg.reply_text(f"✅ Global default theme set to <b>{THEMES[chosen]['name']}</b>!", parse_mode="HTML")

