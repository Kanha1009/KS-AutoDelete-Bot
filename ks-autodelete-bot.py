import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Default delete delay (3 minutes)
DELETE_DELAY_SECONDS = int(os.environ.get("DELETE_DELAY_SECONDS", 180))

# Get bot token from environment variable
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")

# Allowed group IDs (optional, comma-separated in env)
ALLOWED_CHAT_IDS = os.environ.get("ALLOWED_CHAT_IDS")
if ALLOWED_CHAT_IDS:
    ALLOWED_CHAT_IDS = [int(cid.strip()) for cid in ALLOWED_CHAT_IDS.split(",")]
else:
    ALLOWED_CHAT_IDS = None


# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Auto-delete bot active! Messages will vanish after 3 minutes (except pinned ones)."
    )


async def set_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global DELETE_DELAY_SECONDS
    try:
        delay = int(context.args[0])
        DELETE_DELAY_SECONDS = delay * 60 if delay < 100 else delay
        await update.message.reply_text(f"⏱ Delete timer updated: {DELETE_DELAY_SECONDS} seconds")
    except Exception:
        await update.message.reply_text("❌ Usage: /settimer <minutes or seconds>")


async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = update.message.chat_id
    message_id = update.message.message_id

    # Skip if allowed chat IDs specified and current chat not in list
    if ALLOWED_CHAT_IDS and chat_id not in ALLOWED_CHAT_IDS:
        return

    # Skip pinned messages
    if update.message.pinned_message or update.message.is_topic_message:
        return

    # Schedule deletion
    await asyncio.sleep(DELETE_DELAY_SECONDS)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logger.warning(f"Failed to delete message {message_id}: {e}")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"ℹ️ Current auto-delete timer: {DELETE_DELAY_SECONDS} seconds\n"
        f"Allowed chats: {ALLOWED_CHAT_IDS if ALLOWED_CHAT_IDS else 'All'}"
    )


# --- Main entry point ---
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("settimer", set_timer))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, auto_delete))

    application.run_polling()


if __name__ == "__main__":
    main()
