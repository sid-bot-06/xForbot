import asyncio
import logging
import os
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Get bot token from environment
TOKEN = os.getenv("BOT_TOKEN", "7850825321:AAHxoPdkBCfDxlz95_1q3TqEw-YAVb2w5gE")

# Initialize database
DB_FILE = "affiliate.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        joins INTEGER DEFAULT 0,
        balance REAL DEFAULT 0.0
    )''')
    conn.commit()
    conn.close()

init_db()

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username or user.first_name
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user.id, username))
    conn.commit()
    conn.close()

    # Personal referral link
    referral_link = f"https://t.me/xForium?start={user.id}"

    # Main menu
    keyboard = [
        [InlineKeyboardButton("👤 Joins", callback_data="joins")],
        [InlineKeyboardButton("📊 Tier System", callback_data="tiers")],
        [InlineKeyboardButton("🥇 Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("🆘 Support", url="https://t.me/xfAffiliateManager")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Welcome {username}!\n\nYour affiliate link:\n{referral_link}", reply_markup=reply_markup)

# Callback for menu buttons
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if data == "joins":
        c.execute("SELECT joins FROM users WHERE user_id=?", (query.from_user.id,))
        joins = c.fetchone()[0] if c.fetchone() else 0
        earnings = 0  # Placeholder; could calculate based on tiers
        text = f"👤 Joins\n\nYou have {joins} joins.\nRank: Tier 0\nEarnings: £{earnings:.2f}\n\nJoins reset every week."
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back")]]
    elif data == "tiers":
        text = (
            "📊 Tier System\n\n"
            "Tier 1: Reach 25 invites\n£1.00 per member\n\n"
            "Tier 2: Reach 50 invites\n£1.50 per member\n\n"
            "Tier 3: Reach 100 invites\n£2.00 per member"
        )
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back")]]
    elif data == "leaderboard":
        c.execute("SELECT username, joins FROM users ORDER BY joins DESC LIMIT 5")
        top_users = c.fetchall()
        leaderboard_text = "\n".join([f"{i+1}) {user[0]} - {user[1]}" for i, user in enumerate(top_users)]) or "No data yet."
        text = f"🥇 Leaderboard\n\nTop 5 joins:\n{leaderboard_text}\n\nAppear on the top 5 leaderboard for a bonus!"
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back")]]
    elif data == "balance":
        c.execute("SELECT balance FROM users WHERE user_id=?", (query.from_user.id,))
        balance = c.fetchone()[0] if c.fetchone() else 0
        text = f"💰 You have a balance of £{balance:.2f} ready to payout."
        keyboard = [
            [InlineKeyboardButton("Request Payout", callback_data="payout")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back")]
        ]
    elif data == "back":
        text = "Main Menu"
        keyboard = [
            [InlineKeyboardButton("👤 Joins", callback_data="joins")],
            [InlineKeyboardButton("📊 Tier System", callback_data="tiers")],
            [InlineKeyboardButton("🥇 Leaderboard", callback_data="leaderboard")],
            [InlineKeyboardButton("💰 Balance", callback_data="balance")],
            [InlineKeyboardButton("🆘 Support", url="https://t.me/xfAffiliateManager")]
        ]
    else:
        text = "Invalid option."
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back")]]

    conn.close()
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Run bot
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_callback))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
