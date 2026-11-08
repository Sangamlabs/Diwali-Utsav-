# 🪔 Shubh Deepavali - Telegram Festive Bot

An interactive, feature-packed Telegram Bot built with **Python 3.11** & **python-telegram-bot v21** (Async), with **MongoDB Atlas** integration and instant **Local JSON fallback** for frictionless local testing.

---

## ✨ Features

### 🪔 1. Festive Interactions
- **`/diya`**: Light a sacred Diya with festive quotes, beautiful image cards, and claim **200 to 600 bonus coins** (60s cooldown).
- **`/diwali`**: Burst random explosive firecrackers (Sutli Bomb, Sky Shot Rocket, Golden Anar, Laxmi Bomb, Spinning Chakri) with sound effects and images.
- **`/wish [reply or @user]`**: Send personalized, warm festive wishes to any group member with rich greeting images.
- **`/mithai [reply or @user]`**: Feed delicious Indian festive sweets (Kaju Katli, Motichoor Ladoo, Gulab Jamun, Rasgulla, Jalebi) to friends.

### 💰 2. Economy & Rewards
- **`/daily`**: Claim **5,000 coins** every 24 hours.
- **`/loot`**: Claim **10,000 coins** (default 6h cooldown, dynamically adjustable by admin!).
- **`/balance` / `/profile` / `/me`**: Check coins, festive rank titles, inventory of received gifts, and sharing statistics.
- **`/top` / `/leaderboard`**: Interactive live rankings for **Richest Players**, **Top Gifters**, and **Top Wishers**.

### 🎁 3. Gifting System
- **`/gift [reply or @user]`**: Open an interactive inline keyboard of gifts with real-time coin balance check.
- **`/shop`**: Browse the full festive bazaar catalogue with coin prices.
- **Gifts Catalogue**:
  - 🟡 Motichoor Ladoo (1,000 Coins)
  - ✨ Kaju Katli Box (2,500 Coins)
  - 🎇 Electric Sparklers (5,000 Coins)
  - 🌋 Golden Flowerpot Anar (8,000 Coins)
  - 🚀 Mega Rocket Pack (12,000 Coins)
  - 💣 Laxmi Bomb & Sutli (20,000 Coins)
  - 🪙 Shubh Laxmi Gold Coin (50,000 Coins)

### 💥 4. Group Chat Activity & Auto-Spawns
- Monitors active group messages.
- After every **5 messages** (configurable per group), triggers:
  - **Interactive Surprise Drops**: An interactive button `[ 🎁 Claim X Coins! ]` spawns. Fastest finger wins!
  - **Aesthetic Festive Bursts**: Random firecracker explosions or diya illumination broadcasts with high-res photos.

### 👑 5. Full Admin Controls
- **`/admin`**: View complete admin documentation.
- **`/fdrop <coins> [max_claims]`**: Force-spawn an interactive drop in the current chat.
- **`/fdropall <coins> [max_claims]`**: Force-spawn an interactive drop across **all** registered groups!
- **`/fdrop_custom coins | slots | btn_text | img_url | message`**: Dispatches 100% custom-styled drops.
- **`/fspawn [diya|bomb|fireworks|cracker]`**: Force-spawn festive bursts in current chat (or `/fspawnall` for all chats).
- **`/setlootcooldown <hours>`**: Dynamically adjust `/loot` cooldown on the fly without restarting the bot!
- **`/setlootcoins <coins>`**: Dynamically adjust `/loot` reward.
- **`/setdailycoins <coins>`**: Dynamically adjust `/daily` reward.
- **`/setgroupmin <count>`**: Adjust message threshold for group auto-spawns.
- **`/givecoins <user or reply> <amount>`**: Grant coins to any user.
- **`/takecoins <user or reply> <amount>`**: Deduct coins from any user.
- **`/broadcast <message>`**: Send festive announcements to all users and groups.
- **`/stats`**: View total users, groups, coin supply, and database mode.

---

## 🛠️ Project Structure

```
Diwali/
├── config.py             # Image URLs, cooldowns, rewards, gift catalogue
├── main.py               # Application entrypoint & handler registry
├── bot.py                # Alias runner
├── database/
│   ├── __init__.py
│   └── db.py             # Async database (MongoDB + Local JSON fallback)
├── handlers/
│   ├── __init__.py
│   ├── start.py          # /start & /help
│   ├── festive.py        # /diya, /diwali, /wish, /mithai
│   ├── economy.py        # /daily, /loot, /profile, /top
│   ├── gift.py           # /gift, /shop & inline gifting
│   ├── group_activity.py # 5-message counter & interactive drops
│   ├── admin.py          # Full admin control commands
│   └── callbacks.py      # Interactive inline query dispatchers
├── utils/
│   ├── __init__.py
│   └── helpers.py        # Cooldown checkers, mention formatters, image pickers
├── data/                 # Stores local_db.json during local testing
├── .env.example          # Environment variables template
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container deployment definition
├── Procfile              # Railway / Heroku worker definition
└── railway.json          # Railway configuration
```

---

## 🚀 Local Testing Setup

1. **Clone or navigate to the folder:**
   ```bash
   cd "c:\Users\Ayush\Downloads\Telegram Bots\Diwali"
   ```

2. **Create a `.env` file:**
   Copy `.env.example` to `.env`:
   ```env
   BOT_TOKEN=YOUR_BOT_TOKEN_FROM_BOTFATHER
   ADMIN_IDS=YOUR_TELEGRAM_USER_ID
   MONGO_URI=
   ```
   > 💡 **Notice:** Leave `MONGO_URI` blank for local testing! The bot will automatically use `data/local_db.json` so you can test right away without installing MongoDB!

3. **Run the bot:**
   ```bash
   python main.py
   ```

---

## 🚀 Deployment Options

### 1. 🚆 Railway.app (Recommended)
1. Push your repository to GitHub.
2. Go to [Railway.app](https://railway.app), click **New Project** -> **Deploy from GitHub repo**.
3. Under **Variables**, set:
   - `BOT_TOKEN`: `9076278449:AAHaGdcX6RSGc5WoGZMAijWUO3WEfaDv-34`
   - `OWNER_ID`: `8055084559`
   - `ADMIN_IDS`: `8055084559,5852353173`
   - `MONGO_URI`: (Optional) Your MongoDB Atlas connection string (or leave blank for persistent local storage).
4. Railway will automatically detect `railway.json` and `Dockerfile` to deploy your bot 24/7.

### 2. 🌐 Render.com
1. Create a **New Background Worker** on [Render.com](https://render.com).
2. Connect your GitHub repository.
3. Set the environment to **Python 3**.
4. Set Build Command: `pip install -r requirements.txt`
5. Set Start Command: `python main.py`
6. Add environment variables (`BOT_TOKEN`, `OWNER_ID`, `ADMIN_IDS`, `MONGO_URI`).

### 3. 🐳 Docker Container
```bash
# Build the image
docker build -t diwali-bot .

# Run the container
docker run -d --name diwali-bot --env-file .env diwali-bot
```

### 4. 🖥️ VPS / Ubuntu Server
```bash
# Clone and enter directory
cd Diwali

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run in background via PM2 or Systemd
pm2 start main.py --name diwali-bot --interpreter python3
```

