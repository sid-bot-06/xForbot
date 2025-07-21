import os, asyncio, sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

DB = "database.db"
ADMIN = "@xfAffiliateManager"
COMMUNITY = "https://t.me/xForium"

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY, joins INTEGER DEFAULT 0, balance REAL DEFAULT 0
    )""")
    conn.commit()
    conn.close()

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    init_db()
    user = update.effective_user
    conn = sqlite3.connect(DB); cur=conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user.id,))
    conn.commit(); conn.close()
    link = f"https://t.me/xForium?start={user.id}"
    await update.message.reply_text(
        f"👋 Welcome!\nYour personal invite link:\n{link}",
        reply_markup=menu_keyboard()
    )

def menu_keyboard():
    kb = [
        [InlineKeyboardButton("👥 Joins", callback_data="joins"),
         InlineKeyboardButton("📊 Tier System", callback_data="tier")],
        [InlineKeyboardButton("🥇 Leaderboard", callback_data="leader"),
         InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("💬 Support", url=f"https://t.me/{ADMIN}")],
    ]
    return InlineKeyboardMarkup(kb)

async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    uid = query.from_user.id
    conn=sqlite3.connect(DB); cur=conn.cursor()
    if query.data=="joins":
        cur.execute("SELECT joins,balance FROM users WHERE user_id=?", (uid,))
        joins, bal = cur.fetchone() or (0,0)
        await query.edit_message_text(
            f"👤 Joins\nYou have {joins} joins.\nBalance: £{bal:.2f}\nRank: Tier 0\n\nJoins reset every week.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data="menu")]])
        )
    elif query.data=="tier":
        await query.edit_message_text(
            "📊 Tier System\n\nTier 1: Reach 25 invites – £1.00/member\n"
            "Tier 2: Reach 50 invites – £1.50/member\n"
            "Tier 3: Reach 100 invites – £2.00/member",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data="menu")]])
        )
    elif query.data=="leader":
        cur.execute("SELECT user_id,joins FROM users ORDER BY joins DESC LIMIT 5")
        top = cur.fetchall()
        msg = "🥇 Leaderboard\n\nTop 5 joins:\n" + "\n".join(
            f"{i+1}) {uid} – {j}" for i,(uid,j) in enumerate(top))
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data="menu")]]))
    elif query.data=="balance":
        cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
        bal = cur.fetchone()[0]
        await query.edit_message_text(
            f"💰 Your balance: £{bal:.2f}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➡️ Request Payout", callback_data="payout")],
                [InlineKeyboardButton("◀️ Back", callback_data="menu")]
            ])
        )
    elif query.data=="payout":
        await query.edit_message_text("✅ Payout requested! We will process it soon.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data="menu")]]))
    elif query.data=="menu":
        await query.edit_message_text("Main menu:", reply_markup=menu_keyboard())
    conn.commit(); conn.close()

async def adminweekly(context: ContextTypes.DEFAULT_TYPE):
    conn=sqlite3.connect(DB); cur=conn.cursor()
    users = cur.execute("SELECT user_id,joins,balance FROM users").fetchall()
    for uid,joins,bal in users:
        await context.bot.send_message(chat_id=uid,
            text=f"Your total joins this week:\nJoins: {joins}\nEarnings: £{bal:.2f}")
        cur.execute("UPDATE users SET joins=0 WHERE user_id=?", (uid,))
    conn.commit(); conn.close()

async def main():
    init_db()
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))
    app.job_queue.run_repeating(adminweekly, interval=7*24*3600, first=10)
    print("Bot is running...")
    await app.run_polling()

if __name__=="__main__":
    asyncio.run(main())
