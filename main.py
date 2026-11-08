import sys
import logging
from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
import config
from database import db
from utils import init_admins_cache
from handlers import (
    start_handler,
    help_handler,
    diya_handler,
    diwali_handler,
    wish_handler,
    mithai_handler,
    daily_handler,
    loot_handler,
    profile_handler,
    leaderboard_handler,
    gift_command_handler,
    gift_callback_handler,
    my_gifts_handler,
    group_message_tracker,
    claim_drop_callback_handler,
    admin_menu_handler,
    force_drop_handler,
    force_drop_all_handler,
    force_drop_custom_handler,
    force_spawn_handler,
    force_spawn_all_handler,
    set_loot_cooldown_handler,
    set_loot_coins_handler,
    set_daily_coins_handler,
    set_group_min_handler,
    pay_coins_handler,
    add_coins_admin_handler,
    take_coins_admin_handler,
    set_coins_admin_handler,
    broadcast_handler,
    stats_handler,
    add_image_handler,
    del_image_handler,
    list_images_handler,
    list_categories_handler,
    reset_images_handler,
    add_admin_handler,
    del_admin_handler,
    list_admins_handler,
    users_list_handler,
    user_info_admin_handler,
    bot_info_admin_handler,
    groups_list_handler,
    general_callback_handler,
    phod_game_handler,
    phod_callback_handler,
    roll_game_handler,
    slot_game_handler,
    dart_game_handler,
    games_menu_handler,
    lifafa_handler,
    lifafa_callback_handler,
    group_diya_handler,
    quiz_handler,
    quiz_callback_handler,
    theme_command_handler,
    theme_callback_handler,
    admin_set_theme_handler
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)

async def post_init(application):
    """Run database initialization and pre-flight checks."""
    await db.init()
    await init_admins_cache()
    bot_info = await application.bot.get_me()

    # Automatically set bot command menu in Telegram UI
    commands = [
        BotCommand("start", "Start the bot & welcome menu"),
        BotCommand("diya", "Light a holy diya & get coins 🪔"),
        BotCommand("diwali", "Burst a random pataka 💥"),
        BotCommand("wish", "Send Diwali wishes to a friend 💌"),
        BotCommand("gift", "Send sweets & gifts to friends 🎁"),
        BotCommand("mygifts", "View received gifts & senders 🎁"),
        BotCommand("mithai", "Feed delicious sweets to someone 🍬"),
        BotCommand("daily", "Claim 5,000 daily coins 🪙"),
        BotCommand("loot", "Claim 10,000 loot coins 💰"),
        BotCommand("pay", "Transfer coins to a friend 💸"),
        BotCommand("profile", "Check your coins & inventory 🎒"),
        BotCommand("theme", "Aesthetic UI fonts & theme studio 🎨"),
        BotCommand("top", "View richest players & top gifters 🏆"),
        BotCommand("games", "Festive games arcade & rules 🎮"),
        BotCommand("phod", "Live cracker burst gamble 🧨"),
        BotCommand("roll", "Roll 3D sacred Lakshmi dice 🎲"),
        BotCommand("spin", "3D animated slot machine 🎰"),
        BotCommand("dart", "3D bullseye dart target shoot 🎯"),
        BotCommand("lifafa", "Drop festive Shagun packet in group 🧧"),
        BotCommand("quiz", "Diwali knowledge trivia quiz 🧠"),
        BotCommand("groupdiya", "Group community diya goal 🪔"),
        BotCommand("shop", "Browse festive gift shop 🛍️"),
        BotCommand("help", "All commands & guide 📜"),
    ]
    try:
        await application.bot.set_my_commands(commands)
    except Exception as e:
        logger.warning(f"Failed to set bot commands: {e}")

    print("=" * 60)
    print(f"✨ DIWALI BOT STARTED SUCCESSFULLY!")
    print(f"🤖 Bot Name: {bot_info.first_name}")
    print(f"🔗 Bot Username: @{bot_info.username}")
    print(f"👑 Configured Admins: {config.ADMIN_IDS}")
    print(f"📦 Default Loot Cooldown: {config.DEFAULT_LOOT_COOLDOWN_HOURS} hours")
    print("=" * 60)

def main():
    if not config.BOT_TOKEN:
        print("\n❌ ERROR: BOT_TOKEN is missing!")
        print("Please create a .env file and set your BOT_TOKEN:")
        print("BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz\n")
        sys.exit(1)

    # Initialize application
    app = (
        ApplicationBuilder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # --- User Commands ---
    app.add_handler(CommandHandler(["start"], start_handler))
    app.add_handler(CommandHandler(["help"], help_handler))
    app.add_handler(CommandHandler(["diya"], diya_handler))
    app.add_handler(CommandHandler(["diwali"], diwali_handler))
    app.add_handler(CommandHandler(["wish"], wish_handler))
    app.add_handler(CommandHandler(["mithai"], mithai_handler))
    app.add_handler(CommandHandler(["daily"], daily_handler))
    app.add_handler(CommandHandler(["loot"], loot_handler))
    app.add_handler(CommandHandler(["pay", "transfer", "sendcoins"], pay_coins_handler))
    app.add_handler(CommandHandler(["balance", "profile", "me"], profile_handler))
    app.add_handler(CommandHandler(["top", "leaderboard"], leaderboard_handler))
    app.add_handler(CommandHandler(["gift", "gifts", "shop"], gift_command_handler))
    app.add_handler(CommandHandler(["mygifts", "receivedgifts", "giftbox", "giftsreceived", "giftslist"], my_gifts_handler))
    app.add_handler(CommandHandler(["games", "game", "arcade"], games_menu_handler))
    app.add_handler(CommandHandler(["phod", "pataka"], phod_game_handler))
    app.add_handler(CommandHandler(["roll", "dice"], roll_game_handler))
    app.add_handler(CommandHandler(["spin", "slot"], slot_game_handler))
    app.add_handler(CommandHandler(["dart", "darts"], dart_game_handler))
    app.add_handler(CommandHandler(["lifafa"], lifafa_handler))
    app.add_handler(CommandHandler(["groupdiya"], group_diya_handler))
    app.add_handler(CommandHandler(["quiz"], quiz_handler))
    app.add_handler(CommandHandler(["theme", "font", "fonts"], theme_command_handler))

    # --- Admin Commands ---
    app.add_handler(CommandHandler(["admin", "adminhelp"], admin_menu_handler))
    app.add_handler(CommandHandler(["settheme"], admin_set_theme_handler))
    app.add_handler(CommandHandler(["fdrop"], force_drop_handler))
    app.add_handler(CommandHandler(["fdropall"], force_drop_all_handler))
    app.add_handler(CommandHandler(["fdrop_custom"], force_drop_custom_handler))
    app.add_handler(CommandHandler(["fspawn"], force_spawn_handler))
    app.add_handler(CommandHandler(["fspawnall"], force_spawn_all_handler))
    app.add_handler(CommandHandler(["setlootcooldown"], set_loot_cooldown_handler))
    app.add_handler(CommandHandler(["setlootcoins"], set_loot_coins_handler))
    app.add_handler(CommandHandler(["setdailycoins"], set_daily_coins_handler))
    app.add_handler(CommandHandler(["setgroupmin"], set_group_min_handler))
    app.add_handler(CommandHandler(["addcoins", "givecoins", "mintcoins"], add_coins_admin_handler))
    app.add_handler(CommandHandler(["takecoins", "deductcoins"], take_coins_admin_handler))
    app.add_handler(CommandHandler(["setcoins"], set_coins_admin_handler))
    app.add_handler(CommandHandler(["broadcast"], broadcast_handler))
    app.add_handler(CommandHandler(["stats"], stats_handler))
    app.add_handler(CommandHandler(["categories", "imagecategories", "imgcategories", "cats"], list_categories_handler))
    app.add_handler(CommandHandler(["addimage", "setimage"], add_image_handler))
    app.add_handler(CommandHandler(["delimage"], del_image_handler))
    app.add_handler(CommandHandler(["listimages", "getimages"], list_images_handler))
    app.add_handler(CommandHandler(["resetimages"], reset_images_handler))
    app.add_handler(CommandHandler(["addadmin"], add_admin_handler))
    app.add_handler(CommandHandler(["deladmin"], del_admin_handler))
    app.add_handler(CommandHandler(["admins", "listadmins"], list_admins_handler))
    app.add_handler(CommandHandler(["users", "listusers"], users_list_handler))
    app.add_handler(CommandHandler(["userinfo", "uinfo", "info"], user_info_admin_handler))
    app.add_handler(CommandHandler(["botinfo"], bot_info_admin_handler))
    app.add_handler(CommandHandler(["groups", "listgroups"], groups_list_handler))

    # --- Callback Query Handlers ---
    app.add_handler(CallbackQueryHandler(claim_drop_callback_handler, pattern=r"^claim_drop:"))
    app.add_handler(CallbackQueryHandler(lifafa_callback_handler, pattern=r"^open_lifafa:"))
    app.add_handler(CallbackQueryHandler(quiz_callback_handler, pattern=r"^quiz_ans:"))
    app.add_handler(CallbackQueryHandler(gift_callback_handler, pattern=r"^(gift_send:|gift_inspect:|shop_view|cancel_action)"))
    app.add_handler(CallbackQueryHandler(theme_callback_handler, pattern=r"^set_theme_user:"))
    app.add_handler(CallbackQueryHandler(phod_callback_handler, pattern=r"^phod_"))
    app.add_handler(CallbackQueryHandler(general_callback_handler, pattern=r"^(nav_home|help_menu|help_user|help_games|help_groups|help_admin|view_cats_info|admin_view_cats|cat_inspect:|trigger_diya|help_gift|view_my_gifts|lb_|game_start_|view_profile_|theme_menu|users_page:|groups_page:|admin_botinfo)"))

    # --- Group Activity Tracker (Text messages only, non-commands) ---
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & (~filters.COMMAND) & filters.TEXT, group_message_tracker))

    # Error handler
    app.add_error_handler(error_handler)

    print("🚀 Starting polling...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

