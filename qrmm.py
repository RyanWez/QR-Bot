import logging
import qrcode
import io
import uuid
import os
import signal
from urllib.parse import quote
from dotenv import load_dotenv
import asyncio
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

# New imports for OpenCV
import cv2
import numpy as np

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, InlineQueryHandler
from telegram.constants import ChatAction

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.WARNING
)
logger = logging.getLogger(__name__)

# Get configuration from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BOT_NAME = os.getenv('BOT_NAME', 'QR MM Bot')
BOT_USERNAME = os.getenv('BOT_USERNAME', 'qrmmbot')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PORT = int(os.getenv('PORT', 8080))
HOST = os.getenv('HOST', '0.0.0.0')

# Validate required environment variables
if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
    raise ValueError("TELEGRAM_BOT_TOKEN is required. Please check your .env file.")

# User activity tracking for memory optimization
import time
from collections import defaultdict

user_last_activity = defaultdict(float)

# Memory cleanup function
def cleanup_inactive_users():
    """Clean up inactive users to save memory"""
    current_time = time.time()
    inactive_threshold = 1800  # 30 minutes - more aggressive cleanup
    
    inactive_users = [
        user_id for user_id, last_activity in user_last_activity.items()
        if current_time - last_activity > inactive_threshold
    ]
    
    for user_id in inactive_users:
        user_last_activity.pop(user_id, None)
    
    if inactive_users:
        logger.info(f"Cleaned up {len(inactive_users)} inactive users")

# --- Command Handlers ---
async def start_command(update: Update, context) -> None:
    user = update.effective_user
    welcome_message = f"""မင်္ဂလာပါ {user.first_name}! 👋

🤖 ကျွန်တော်က QR Code Bot ပါ။

*🎯 အသုံးပြုပုံ:*
• `*QR Code ဖန်တီးရန်* - စာ၊ link၊ emoji စတာတွေကို ပို့ပေးပါ၊ ကျွန်တော်က QR ဖန်တီး‌ပေးပါမယ်။`
• `*QR Code ဖတ်ရန်* - QR Code ပါတဲ့ ဓာတ်ပုံကို ပို့ပေးပါ၊ QR Code ထဲမှာ ပါတဲ့ အကြောင်းအရာတွေကို ကျွန်တော် ပြန်ပို့ပေးပါမယ်။`


*💡Commands:*
/help - အကူအညီ
/update - နောက်ဆုံး Update များ

*🚀 Rock!*"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context) -> None:
    help_text = """
🤖 *QR Code Bot အသုံးပြုပုံ*

*🎯 အလွယ်တကူ အသုံးပြုနည်း:*

*1. QR Code ဖန်တီးရန်* 🎨
• စာ၊ link၊ emoji၊ နံပါတ် စတာတွေကို တိုက်ရိုက်ပို့လိုက်ပါ
• ဥပမာ: `Hello World`, `https://google.com`, `09123456789`

*2. QR Code ဖတ်ရန်* 📸
• QR Code ပါတဲ့ ဓာတ်ပုံကို ပို့လိုက်ပါ
• Bot က အလိုအလျောက် ဖတ်ပေးမယ်

*🔧 Commands:*
/start - Bot ကို စတင်အသုံးပြုရန်
/help - အကူအညီ ရယူရန်
/update - နောက်ဆုံး Update များကြည့်ရန်

*💡 Tips:*
• Link တွေမှာ `https://` ပါရင် ကောင်းပါတယ်
• `အကောင်းဆုံးကတော့ အစထဲက မတွေ့ခဲ့ကြရင်ပေါ့...`
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def update_command(update: Update, context) -> None:
    """Show bot updates and changelog"""
    changelog_text = """
🚀 *QR MM Bot - Updates & Changelog*

*📅 v2.0 - August 14, 2025* 🎉
• 🔥 *Major Update*
• ❌ Inline button တွေကို ဖြုတ်လိုက်ပါပြီ
• 🤖 *Smart Detection* - အလိုအလျောက် သိနိုင်ပါပြီ
  - Text or Link ပို့ရင် → QR Code ဖန်တီးမယ်
  - ဓာတ်ပုံ ပို့ရင် → QR Code ဖတ်မယ်
• ⚡ ပိုမြန်၊ ပိုလွယ်ကူအောင် ပြုလုပ်ထားပါတယ်
• 💬 Typing action ထည့်ထားပါတယ်
• 🎯 /start နှိပ်ပြီး တန်းသုံးလို့ရပါပြီ

*📅 v1.02 - August 13, 2025*
• ✅ Reply functionality ထည့်ပြီးပါပြီ
• 🔄 QR Code ပြန်လုပ်ပြီးတဲ့အခါ original message ကို reply ပြန်ပေးမယ်
• 📝 /update command ထည့်ပြီးပါပြီ
• ❓ Unknown commands အတွက် helpful response

*📅 v1.01 - August 12, 2025*
• 🎨 QR Code generation ပိုမြန်အောင် optimize လုပ်ပြီးပါပြီ
• 📝 Op enCV နဲ့ QR Code reading ပိုတိကျအောင် ပြုပြင်ပြီးပါပြီ

*📅 v1.00 - August 11, 2025*
• 🎉 QR MM Bot ကို စတင်အသုံးပြုနိုင်ပါပြီ
• 🎨 QR Code ဖန်တီးခြင်း feature
• 📸 QR Code ဖတ်ခြင်း feature
• 🔄 Inline mode support
• 🇲🇲 Myanmar language support

*🔮 Coming Soon:*
• 📊 QR Code analytics
• 🎨 Custom QR Code designs
• 📱 Batch QR Code generation

*👨‍💻 Dev:* @RyanWez
*GitHub:* `Coming Soon...`
    """
    await update.message.reply_text(changelog_text, parse_mode='Markdown')

async def unknown_command(update: Update, context) -> None:
    """Handle unknown commands"""
    command = update.message.text
    
    unknown_text = f"""
❓ *မသိရှိသော Command*

`{command}` ဆိုတဲ့ command ကို မသိရှိပါဘူး။

*✅ အသုံးပြုနိုင်တဲ့ Commands:*
/start - Bot ကို စတင်အသုံးပြုရန်
/help - အကူအညီ ရယူရန်
/update - နောက်ဆုံး Update များကြည့်ရန်

    """
    await update.message.reply_text(unknown_text, parse_mode='Markdown')


# --- Message Handlers ---
async def handle_text_message(update: Update, context) -> None:
    user_id = update.effective_user.id
    text = update.message.text
    
    # Update user activity
    user_last_activity[user_id] = time.time()
    
    # Periodic cleanup (every 100 requests)
    if len(user_last_activity) % 100 == 0:
        cleanup_inactive_users()
    
    # Smart detection: Text/Link = Create QR Code automatically
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    
    try:
        # Generate QR code with optimized settings for speed and size
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,  # Lowest error correction for smaller size
            box_size=8,  # Smaller box size for faster generation
            border=2,    # Smaller border
        )
        qr.add_data(text)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        bio = io.BytesIO()
        bio.name = 'qr_code.png'
        # Optimize PNG for smaller file size and faster upload
        qr_img.save(bio, 'PNG', optimize=True, compress_level=9)
        bio.seek(0)
        
        # Try to send photo with better error handling
        try:
            await context.bot.send_photo(
                chat_id=update.message.chat_id, 
                photo=bio, 
                caption=f"✅ *QR Code ဖန်တီးပြီးပါပြီ*\n\n📝 *အချက်အလက်:* `{text}`\n\n💡 *Tip:* QR Code ဖတ်ချင်ရင် ဓာတ်ပုံ ပို့လိုက်ပါ",
                parse_mode='Markdown',
                reply_to_message_id=update.message.message_id
            )
        except Exception as send_error:
            logger.error(f"Error sending photo: {send_error}")
            # If photo sending fails, send text message
            await update.message.reply_text(
                f"✅ *QR Code ဖန်တီးပြီးပါပြီ*\n\n📝 *အချက်အလက်:* `{text}`\n\n⚠️ ဓာတ်ပုံ ပို့ရာတွင် ပြဿနာရှိနေပါတယ်။ Network connection ကို စစ်ကြည့်ပါ။",
                parse_mode='Markdown',
                reply_to_message_id=update.message.message_id
            )
            
    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
        await update.message.reply_text(
            "❌ QR Code ဖန်တီးရာတွင် အမှားတစ်ခုဖြစ်ပွားသွားပါတယ်။ Network connection ကို စစ်ကြည့်ပြီး ထပ်ကြိုးစားကြည့်ပါ။",
            reply_to_message_id=update.message.message_id
        )

async def handle_photo_message(update: Update, context) -> None:
    user_id = update.effective_user.id
    
    # Update user activity
    user_last_activity[user_id] = time.time()
    
    # Smart detection: Photo = Read QR Code automatically
    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        photo_file = await update.message.photo[-1].get_file()
        
        # Download the photo to a byte array in memory
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Convert byte array to a NumPy array
        np_array = np.frombuffer(photo_bytes, np.uint8)
        
        # Decode the NumPy array into an image
        img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if img is None:
            await update.message.reply_text(
                "❌ *ဓာတ်ပုံ ဖတ်၍မရပါ*\n\nဓာတ်ပုံကို ဖတ်လို့မရပါဘူး။ တခြားပုံတစ်ပုံကို ထပ်ပို့ကြည့်ပါ။\n\n💡 *Tip:* QR Code ဖန်တီးချင်ရင် စာ သို့ link ပို့လိုက်ပါ",
                parse_mode='Markdown',
                reply_to_message_id=update.message.message_id
            )
            return

        # Initialize the QRCode detector
        detector = cv2.QRCodeDetector()
        data, vertices, straight_qrcode = detector.detectAndDecode(img)
        
        if data:
            reply_text = f"✅ *QR Code ဖတ်ပြီးပါပြီ*\n\n📋 *တွေ့ရှိသော အချက်အလက်:*\n`{data}`\n\n💡 *Tip:* QR Code ဖန်တီးချင်ရင် စာ သို့ link ပို့လိုက်ပါ"
        else:
            reply_text = "❌ *QR Code မတွေ့ပါ*\n\nဒီပုံထဲမှာ QR Code မတွေ့ပါဘူး။ ရှင်းလင်းတဲ့ QR Code ပုံတစ်ပုံကို ထပ်ပို့ကြည့်ပါ။\n\n💡 *Tips:*\n• QR Code ကို ရှင်းရှင်းလင်းလင်း ရိုက်ပါ\n• အလင်း လုံလောက်အောင် ရိုက်ပါ\n• QR Code တစ်ခုလုံး ပါအောင် ရိုက်ပါ"
        
        await update.message.reply_text(
            reply_text, 
            parse_mode='Markdown',
            reply_to_message_id=update.message.message_id
        )

    except Exception as e:
        logger.error(f"Error decoding QR code with OpenCV: {e}")
        await update.message.reply_text(
            "❌ *QR Code ဖတ်၍မရပါ*\n\nQR Code ကိုဖတ်ရာတွင် အမှားတစ်ခုဖြစ်ပွားသွားပါတယ်။ ထပ်ကြိုးစားကြည့်ပါ။\n\n💡 *Tip:* QR Code ဖန်တီးချင်ရင် စာ သို့ link ပို့လိုက်ပါ",
            parse_mode='Markdown',
            reply_to_message_id=update.message.message_id
        )


async def handle_other_messages(update: Update, context) -> None:
    """Handle other message types (stickers, documents, etc.)"""
    user_id = update.effective_user.id
    
    # Update user activity
    user_last_activity[user_id] = time.time()
    
    # Determine message type for better response
    message_type = "အခြား"
    if update.message.sticker:
        message_type = "Sticker"
    elif update.message.document:
        message_type = "Document"
    elif update.message.video:
        message_type = "Video"
    elif update.message.audio:
        message_type = "Audio"
    elif update.message.voice:
        message_type = "Voice message"
    elif update.message.location:
        message_type = "Location"
    elif update.message.contact:
        message_type = "Contact"
    
    await update.message.reply_text(
        f"🤔 *{message_type} ကို လက်ခံ၍မရပါ*\n\n*✅ လက်ခံနိုင်သော အမျိုးအစားများ:*\n• 📝 *စာ/Text* - QR Code ဖန်တီးမယ်\n• 🔗 *Link* - QR Code ဖန်တီးမယ်\n• 📸 *ဓာတ်ပုံ* - QR Code ဖတ်မယ်\n\n💡 *အသုံးပြုပုံ:*\n• QR Code ဖန်တီးချင်ရင် → စာ သို့ link ပို့ပါ\n• QR Code ဖတ်ချင်ရင် → ဓာတ်ပုံ ပို့ပါ",
        parse_mode='Markdown',
        reply_to_message_id=update.message.message_id
    )


# --- Callback & Inline Handlers ---
async def button_handler(update: Update, context) -> None:
    """Handle any remaining callback queries (for backward compatibility)"""
    query = update.callback_query
    await query.answer()
    
    # Since we removed inline buttons, just send a helpful message
    await query.message.reply_text(
        "🚀 *Bot ကို အဆင့်မြှင့်တင်ပြီးပါပြီ!*\n\n*✨ အခုတော့ ပိုလွယ်ပါပြီ:*\n• QR Code ဖန်တီးချင်ရင် → စာ သို့ link ပို့လိုက်ပါ\n• QR Code ဖတ်ချင်ရင် → ဓာတ်ပုံ ပို့လိုက်ပါ\n\n*🎯 ခလုတ်တွေ နှိပ်စရာမလို!*",
        parse_mode='Markdown'
    )

async def inline_qr(update: Update, context) -> None:
    query_text = update.inline_query.query
    if not query_text:
        return
    encoded_text = quote(query_text)
    qr_image_url = f"http://api.qrserver.com/v1/create-qr-code/?data={encoded_text}&size=200x200"
    results = [
        InlineQueryResultPhoto(
            id=str(uuid.uuid4()),
            photo_url=qr_image_url,
            thumbnail_url=qr_image_url,
            caption=f"QR Code for: '{query_text}'"
        )
    ]
    await update.inline_query.answer(results, cache_time=10)


# Health check endpoint
async def health_check(request: Request) -> Response:
    """Health check endpoint for Fly.io"""
    try:
        # Simple health check - return bot status
        health_data = {
            "status": "healthy",
            "bot_name": BOT_NAME,
            "timestamp": asyncio.get_event_loop().time()
        }
        return web.json_response(health_data, status=200)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return web.Response(text="UNHEALTHY", status=503)

# Webhook handler
async def webhook_handler(request: Request) -> Response:
    """Handle incoming webhook requests with concurrent processing"""
    try:
        # Get the application from request app
        application = request.app['telegram_app']
        
        # Get update data
        update_data = await request.json()
        update = Update.de_json(update_data, application.bot)
        
        # Process the update asynchronously (non-blocking)
        asyncio.create_task(application.process_update(update))
        
        # Return immediately to Telegram
        return web.Response(status=200)
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return web.Response(status=500)

async def keep_alive_ping(request: Request) -> Response:
    """Keep-alive endpoint to prevent sleeping"""
    return web.Response(text="pong", status=200)

def create_app(application: Application) -> web.Application:
    """Create aiohttp web application"""
    app = web.Application()
    app['telegram_app'] = application
    
    # Add routes
    app.router.add_get('/health', health_check)
    app.router.add_get('/ping', keep_alive_ping)
    app.router.add_post(f'/webhook/{TELEGRAM_TOKEN}', webhook_handler)
    
    return app

async def setup_webhook(application: Application) -> None:
    """Setup webhook for production"""
    if WEBHOOK_URL:
        webhook_url = f"{WEBHOOK_URL}/webhook/{TELEGRAM_TOKEN}"
        await application.bot.set_webhook(webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
    else:
        logger.warning("WEBHOOK_URL not set, webhook not configured")

def setup_handlers(application: Application) -> None:
    """Setup all bot handlers"""
    # Command handlers (specific commands first)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("update", update_command))
    
    # Inline handler for backward compatibility
    application.add_handler(InlineQueryHandler(inline_qr))
    
    # Callback handler for backward compatibility (simplified)
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Message handlers (smart detection)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))
    application.add_handler(MessageHandler(~(filters.TEXT | filters.PHOTO | filters.COMMAND), handle_other_messages))
    
    # Unknown command handler (must be last)
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

def create_application() -> Application:
    """Create telegram application with timeout settings"""
    return (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .build()
    )

async def run_webhook_mode() -> None:
    """Run bot in webhook mode for production"""
    application = create_application()
    setup_handlers(application)
    
    # Initialize the application
    await application.initialize()
    
    logger.info("Starting bot in webhook mode...")
    
    # Setup webhook
    await setup_webhook(application)
    
    # Create web app
    web_app = create_app(application)
    
    # Start the application
    await application.start()
    
    # Run web server
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    await site.start()
    
    logger.info(f"Bot is running on {HOST}:{PORT} with webhook")
    
    # Create shutdown event
    shutdown_event = asyncio.Event()
    
    # Signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        shutdown_event.set()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Keep the application running until shutdown signal
    try:
        await shutdown_event.wait()
    except asyncio.CancelledError:
        logger.info("Received cancellation, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Starting cleanup...")
        try:
            await application.stop()
            await runner.cleanup()
            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def run_polling_mode() -> None:
    """Run bot in polling mode for development"""
    application = create_application()
    setup_handlers(application)
    
    logger.info("Starting bot in polling mode...")
    print("Bot is running in development mode...")
    application.run_polling()

async def main() -> None:
    """Main function - determines run mode"""
    if WEBHOOK_URL:
        await run_webhook_mode()
    else:
        # For development, we don't use async main
        run_polling_mode()

if __name__ == '__main__':
    if WEBHOOK_URL:
        # Production mode with webhook
        asyncio.run(main())
    else:
        # Development mode with polling
        run_polling_mode()