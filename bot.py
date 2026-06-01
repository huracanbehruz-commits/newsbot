import os
import asyncio
import logging
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
from aggregator import NewsAggregator

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN  = os.getenv("TELEGRAM_TOKEN")
TG_API_ID       = int(os.getenv("TG_API_ID", "0"))
TG_API_HASH     = os.getenv("TG_API_HASH", "")
TG_SESSION_STR  = os.getenv("TG_SESSION_STR", "")

aggregator = NewsAggregator(TG_API_ID, TG_API_HASH, TG_SESSION_STR)

TOPICS = {
    "investment": "💰 Investment",
    "startup":    "🚀 Startup",
    "insights":   "🧠 Insights",
    "breakdown":  "🏢 Breakdown",
}

REGIONS = {
    "uz":    "🇺🇿 Uzbekistan",
    "ca":    "🌏 Central Asia",
    "world": "🌍 Worldwide",
}


def region_keyboard(topic: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(label, callback_data=f"{topic}:{region}")
        for region, label in REGIONS.items()
    ]])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 *Welcome to your News Digest Bot!*\n\n"
        "Pick a topic then select a region:\n\n"
        "💰 /investment\n"
        "🚀 /startup\n"
        "🧠 /insights\n"
        "🏢 /breakdown\n"
        "📰 /news — All 4 topics\n\n"
        "_Sources: Telegram channels + local sites_"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def topic_command(update: Update, context: ContextTypes.DEFAULT_TYPE, topic: str):
    await update.message.reply_text(
        f"{TOPICS[topic]} — choose a region:",
        reply_markup=region_keyboard(topic)
    )

async def investment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await topic_command(update, context, "investment")
async def startup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await topic_command(update, context, "startup")
async def insights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await topic_command(update, context, "insights")
async def breakdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await topic_command(update, context, "breakdown")

async def news_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📰 *All Topics* — choose a region:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(label, callback_data=f"all:{region}")
            for region, label in REGIONS.items()
        ]])
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    topic, region = query.data.split(":")
    region_label  = REGIONS.get(region, region)

    if topic == "all":
        await query.edit_message_text(f"📰 Fetching all topics · {region_label}...")
        for t in ["investment", "startup", "insights", "breakdown"]:
            msg = await query.message.reply_text(f"⏳ Fetching {TOPICS[t]}...")
            await _fetch_and_reply(msg, t, region, query.message)
            await asyncio.sleep(1)
    else:
        await query.edit_message_text(f"⏳ Fetching {TOPICS[topic]} · {region_label}...")
        await _fetch_and_reply(query.message, topic, region, query.message)


async def _fetch_and_reply(msg, topic: str, region: str, original):
    try:
        articles = await aggregator.fetch_all(topic, region)
        if not articles:
            await msg.edit_text(
                f"😕 Nothing found for *{TOPICS[topic]}* · {REGIONS[region]} right now. Try again later.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        text = aggregator.format(articles, topic, region)
        for part in _split(text):
            try:
                await msg.edit_text(part, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
                msg = None
            except Exception:
                await original.reply_text(part, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await msg.edit_text("❌ Something went wrong. Please try again.")


def _split(text: str, limit: int = 4000) -> list[str]:
    parts = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut == -1:
            cut = limit
        parts.append(text[:cut])
        text = text[cut:].lstrip("\n")
    parts.append(text)
    return parts


async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("start",      "Welcome & help"),
        BotCommand("news",       "All 4 topics"),
        BotCommand("investment", "Investment & funding"),
        BotCommand("startup",    "Startup & founders"),
        BotCommand("insights",   "Professional insights"),
        BotCommand("breakdown",  "Company & tech breakdowns"),
    ])


def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("Set TELEGRAM_TOKEN env var")

    app = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start",      start))
    app.add_handler(CommandHandler("news",       news_all))
    app.add_handler(CommandHandler("investment", investment))
    app.add_handler(CommandHandler("startup",    startup))
    app.add_handler(CommandHandler("insights",   insights))
    app.add_handler(CommandHandler("breakdown",  breakdown))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Bot started.")
    app.run_polling()


if __name__ == "__main__":
    main()
