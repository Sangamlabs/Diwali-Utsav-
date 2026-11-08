import random
from telegram import Update
from telegram.ext import ContextTypes
from database import db
from utils import (
    get_mention,
    format_number,
    get_random_image
)
from handlers.group_activity import spawn_interactive_drop

GROUP_DIYA_TARGET = 15

async def group_diya_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /groupdiya
    Check group community Diya lighting progress bar and milestone status!
    """
    chat = update.effective_chat
    msg = update.effective_message
    if not chat or not msg:
        return

    if chat.type not in ["group", "supergroup"]:
        await msg.reply_text("🪔 Group Diya Milestone is for group chats! Add me to a group to unite and light diyas together!")
        return

    group = await db.get_group(chat.id, chat.title)
    current_diyas = group.get("group_diyas", 0)
    target = group.get("diya_target", GROUP_DIYA_TARGET)
    completed_rounds = group.get("diya_milestones_completed", 0)

    percent = min(100, int((current_diyas / target) * 100))
    filled_bars = int(percent / 10)
    empty_bars = 10 - filled_bars
    progress_bar = "█" * filled_bars + "░" * empty_bars

    status_text = (
        f"🪔 <b>COMMUNITY DIYA MILESTONE — {chat.title}</b> 🪔\n\n"
        f"Unite as a group to illuminate this chat! Every member who runs <code>/diya</code> contributes a sacred diya to the milestone!\n\n"
        f"📊 <b>Progress:</b> <code>[{progress_bar}]</code> <b>{percent}%</b>\n"
        f"🕯️ <b>Diyas Lit:</b> <code>{current_diyas} / {target}</code>\n"
        f"🏆 <b>Milestones Completed:</b> <code>{completed_rounds}</code> Times\n\n"
        f"✨ <b>Milestone Reward:</b> When <b>{target}</b> diyas are lit, a <b>Maha-Deepavali Coin Drop</b> will spawn for the group!\n\n"
        f"<i>Type <code>/diya</code> right now to contribute your light!</i> 🪔"
    )

    await msg.reply_text(status_text, parse_mode="HTML")

async def record_group_diya(chat_id: int, user_id: int, user_name: str, context: ContextTypes.DEFAULT_TYPE):
    """
    Increment group community diya count.
    If target reached, trigger a grand Maha-Deepavali reward drop!
    """
    group = await db.get_group(chat_id)
    current = group.get("group_diyas", 0) + 1
    target = group.get("diya_target", GROUP_DIYA_TARGET)

    if current >= target:
        # Milestone completed!
        rounds = group.get("diya_milestones_completed", 0) + 1
        await db.update_group(chat_id, {
            "group_diyas": 0,
            "diya_milestones_completed": rounds
        })

        celebration_msg = (
            f"✨🪔🌟 <b>DIVINE MAHA-DEEPAVALI MILESTONE COMPLETED!</b> 🌟🪔✨\n\n"
            f"Spectacular unity! The members of this group have successfully lit <b>{target} Sacred Diyas</b> together!\n\n"
            f"🎆 Darkness has completely vanished and Goddess Lakshmi has showered golden blessings!\n"
            f"🎁 <i>Here is your community celebration treasure drop!</i>"
        )
        try:
            await context.bot.send_message(chat_id=chat_id, text=celebration_msg, parse_mode="HTML")
            # Spawn interactive drop with 3,500 coins for 3 fastest players!
            await spawn_interactive_drop(
                chat_id=chat_id,
                context=context,
                custom_coins=3500,
                max_claims=3,
                custom_msg=(
                    "🪔 <b>MAHA-AARTI COMMUNITY REWARD!</b> 🪔\n\n"
                    "Celebrate your group's completed Diya milestone!\n"
                    "🪙 <b>Prize:</b> <code>3,500</code> Coins each\n"
                    "⚡ <b>Slots:</b> 3 fastest fingers!\n\n"
                    "<i>Tap below right now to claim!</i>"
                )
            )
        except Exception as e:
            print(f"Error triggering milestone celebration: {e}")
    else:
        await db.update_group(chat_id, {"group_diyas": current})

