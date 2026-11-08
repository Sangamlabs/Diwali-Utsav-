import random
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import db
from utils import (
    get_mention,
    format_number,
    check_cooldown,
    format_remaining_time
)

QUIZ_COOLDOWN_SECONDS = 300  # 5 minutes
QUIZ_REWARD_COINS = 1000

QUIZ_QUESTIONS = [
    {
        "id": "q1",
        "question": "After how many years of exile did Lord Rama return to Ayodhya on Diwali?",
        "options": ["12 Years", "14 Years", "16 Years", "10 Years"],
        "correct": 1,
        "explanation": "Lord Rama returned to Ayodhya after 14 years of exile after vanquishing Ravana."
    },
    {
        "id": "q2",
        "question": "Which auspicious festival marks the very first day of the 5-day Diwali celebration?",
        "options": ["Choti Diwali", "Govardhan Puja", "Dhanteras", "Bhai Dooj"],
        "correct": 2,
        "explanation": "Dhanteras marks the arrival of Lord Dhanvantari and Goddess Lakshmi."
    },
    {
        "id": "q3",
        "question": "Which Goddess of wealth, fortune, and prosperity is worshipped on Diwali night?",
        "options": ["Goddess Lakshmi", "Goddess Saraswati", "Goddess Parvati", "Goddess Kali"],
        "correct": 0,
        "explanation": "Goddess Lakshmi, along with Lord Ganesha, is worshipped on Diwali night for prosperity."
    },
    {
        "id": "q4",
        "question": "What is the ancient Sanskrit meaning of the word 'Deepavali'?",
        "options": ["Festival of Joy", "Row of Clay Lamps", "Victory of Light", "Golden Lights"],
        "correct": 1,
        "explanation": "'Deepa' means clay lamp (diya) and 'Avali' means row or series."
    },
    {
        "id": "q5",
        "question": "Which festival celebrated two days after Diwali honors the eternal bond between brothers and sisters?",
        "options": ["Bhai Dooj", "Raksha Bandhan", "Karwa Chauth", "Govardhan Puja"],
        "correct": 0,
        "explanation": "Bhai Dooj (Yama Dwitiya) celebrates the divine bond between brother and sister."
    },
    {
        "id": "q6",
        "question": "Which sacred sweet made from cashew nuts and silver foil is most popular during Diwali?",
        "options": ["Gulab Jamun", "Kaju Katli", "Rasgulla", "Jalebi"],
        "correct": 1,
        "explanation": "Kaju Katli (diamond-shaped cashew fudge) is the royal sweet of Diwali!"
    },
    {
        "id": "q7",
        "question": "In the epic Ramayana, who helped Lord Rama build the floating bridge (Ram Setu) to Lanka?",
        "options": ["Garuda", "The Vanara Army (Nal & Neel)", "The Devas", "The Gandharvas"],
        "correct": 1,
        "explanation": "The Vanara architects Nal and Neel inscribed Lord Rama's name on stones that floated."
    }
]

async def quiz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /quiz - Test your festive knowledge and win 1,000 coins!"""
    user = update.effective_user
    msg = update.effective_message
    if not user or not msg:
        return

    user_data = await db.get_user(user.id, {"username": user.username, "first_name": user.first_name})
    last_quiz = user_data.get("last_quiz")

    is_ready, remaining = check_cooldown(last_quiz, QUIZ_COOLDOWN_SECONDS)
    if not is_ready:
        time_str = format_remaining_time(remaining)
        await msg.reply_text(
            f"🧠 <b>Quiz Cooldown!</b>\n\n"
            f"Hey {get_mention(user)}, you can attempt the next Diwali quiz in: <b>{time_str}</b> 🪔",
            parse_mode="HTML"
        )
        return

    # Pick a random question
    q = random.choice(QUIZ_QUESTIONS)
    q_index = QUIZ_QUESTIONS.index(q)

    caption = (
        f"🧠 <b>SHUBH DIWALI KNOWLEDGE QUIZ</b> 🧠\n\n"
        f"👤 <b>Player:</b> {get_mention(user)}\n"
        f"🪙 <b>Reward:</b> <code>{format_number(QUIZ_REWARD_COINS)}</code> Coins for correct answer!\n\n"
        f"❓ <b>Question:</b>\n"
        f"<b>{q['question']}</b>\n\n"
        f"<i>Select your answer below:</i>"
    )

    buttons = []
    for opt_idx, opt_text in enumerate(q["options"]):
        buttons.append([InlineKeyboardButton(f"{chr(65 + opt_idx)}) {opt_text}", callback_data=f"quiz_ans:{user.id}:{q_index}:{opt_idx}")])

    await msg.reply_text(caption, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons))

async def quiz_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's quiz answer selection."""
    query = update.callback_query
    if not query or not query.data or not query.data.startswith("quiz_ans:"):
        return

    parts = query.data.split(":")
    if len(parts) != 4:
        return

    expected_user_id = int(parts[1])
    q_index = int(parts[2])
    selected_opt = int(parts[3])
    user = query.from_user

    # Only original quiz taker can answer
    if user.id != expected_user_id:
        await query.answer("⚠️ This quiz was generated for another player! Type /quiz to start your own!", show_alert=True)
        return

    if q_index >= len(QUIZ_QUESTIONS):
        return

    q = QUIZ_QUESTIONS[q_index]
    is_correct = (selected_opt == q["correct"])

    # Update quiz timestamp
    await db.update_user(user.id, {"last_quiz": datetime.utcnow().isoformat()})

    mention = get_mention(user)

    if is_correct:
        new_bal = await db.add_coins(user.id, QUIZ_REWARD_COINS)
        await query.answer(f"🎉 Correct Answer! +{format_number(QUIZ_REWARD_COINS)} Coins!", show_alert=True)
        result_text = (
            f"🎉 <b>SHABASH! CORRECT ANSWER!</b> 🧠✨\n\n"
            f"👤 <b>Player:</b> {mention}\n"
            f"❓ <b>Question:</b> {q['question']}\n\n"
            f"✅ <b>Your Answer:</b> <b>{q['options'][selected_opt]}</b>\n"
            f"💡 <i>{q['explanation']}</i>\n\n"
            f"🪙 <b>Prize Won:</b> +<code>{format_number(QUIZ_REWARD_COINS)}</code> Coins\n"
            f"💰 <b>Total Balance:</b> <code>{format_number(new_bal)}</code> Coins\n\n"
            f"<i>Next quiz available in 5 minutes! (/quiz)</i>"
        )
    else:
        correct_ans = q["options"][q["correct"]]
        await query.answer("❌ Oops, that was incorrect!", show_alert=True)
        result_text = (
            f"❌ <b>INCORRECT ANSWER!</b> 🧠\n\n"
            f"👤 <b>Player:</b> {mention}\n"
            f"❓ <b>Question:</b> {q['question']}\n\n"
            f"Selected: <i>{q['options'][selected_opt]}</i>\n"
            f"✅ <b>Correct Answer:</b> <b>{correct_ans}</b>\n\n"
            f"💡 <i>{q['explanation']}</i>\n\n"
            f"<i>Better luck next time! Practice again in 5 minutes with /quiz!</i>"
        )

    try:
        await query.edit_message_text(result_text, parse_mode="HTML")
    except Exception:
        await query.message.reply_text(result_text, parse_mode="HTML")

