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

# User states with memory optimization
import time
from collections import defaultdict

user_states = {}
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
        user_states.pop(user_id, None)
        user_last_activity.pop(user_id, None)
    
    if inactive_users:
        logger.info(f"Cleaned up {len(inactive_users)} inactive users")

# --- Command Handlers ---
async def start_command(update: Update, context) -> None:
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🎨 QR Code ဖန်တီးမယ်", callback_data='create_qr')],
        [InlineKeyboardButton("📸 QR Code ဖတ်မယ်", callback_data='read_qr')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_message = f"မင်္ဂလာပါ {user.first_name}!\n\nကျွန်တော်က QR Code Bot ပါ။ အောက်က ခလုတ်တွေကနေ လိုချင်တဲ့ ဝန်ဆောင်မှုကို ရွေးချယ်နိုင်ပါတယ်"
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def help_command(update: Update, context) -> None:
    help_text = """
    *QR Code Bot အသုံးပြုပုံ*
    *1. QR Code ဖန်တီးရန်*
    - စာ သို့မဟုတ် link တစ်ခုခုကို တိုက်ရိုက် ပို့ပေးလိုက်ပါ။
    *2. QR Code ဖတ်ရန်*
    - QR Code ပါတဲ့ ဓာတ်ပုံတစ်ပုံကို ပို့ပေးလိုက်ပါ။
    
    - *Source Code ရယူရန်*=>`@RyanWez`
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')


# --- Message Handlers ---
async def handle_text_message(update: Update, context) -> None:
    user_id = update.effective_user.id
    text = update.message.text
    
    # Update user activity
    user_last_activity[user_id] = time.time()
    
    # Periodic cleanup (every 100 requests)
    if len(user_last_activity) % 100 == 0:
        cleanup_inactive_users()
    
    # Check user state
    current_state = user_states.get(user_id)
    
    if current_state == 'create_mode':
        # User is in QR creation mode - generate QR code
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
            
            # Only show "QR Code ဖတ်မယ်" button as requested
            keyboard = [
                [InlineKeyboardButton("📸 QR Code ဖတ်မယ်", callback_data='read_qr')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Try to send photo with better error handling
            try:
                await context.bot.send_photo(
                    chat_id=update.message.chat_id, 
                    photo=bio, 
                    caption=f"✅ *QR Code ဖန်တီးပြီးပါပြီ *\n\n *ဒီ* : `{text}` အတွက် QR Code ပါ",
                    parse_mode='Markdown',
                    reply_markup=reply_markup,
                    reply_to_message_id=update.message.message_id
                )
            except Exception as send_error:
                logger.error(f"Error sending photo: {send_error}")
                # If photo sending fails, send text message with retry button
                keyboard = [
                    [InlineKeyboardButton("🔄 ထပ်ကြိုးစားမယ်", callback_data='create_qr')],
                    [InlineKeyboardButton("📸 QR Code ဖတ်မယ်", callback_data='read_qr')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"✅ *QR Code ဖန်တီးပြီးပါပြီ *\n\n *ဒီ* : `{text}` အတွက် QR Code ပါ\n\n⚠️ ဓာတ်ပုံ ပို့ရာတွင် ပြဿနာရှိနေပါတယ်။ Network connection ကို စစ်ကြည့်ပါ။",
                    parse_mode='Markdown',
                    reply_markup=reply_markup,
                    reply_to_message_id=update.message.message_id
                )
                
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            keyboard = [
                [InlineKeyboardButton("🔄 ထပ်ကြိုးစားမယ်", callback_data='create_qr')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "❌ QR Code ဖန်တီးရာတွင် အမှားတစ်ခုဖြစ်ပွားသွားပါတယ်။ Network connection ကို စစ်ကြည့်ပြီး ထပ်ကြိုးစားကြည့်ပါ။",
                reply_markup=reply_markup
            )
            
    elif current_state == 'read_mode':
        # User is in QR reading mode but sent text - show error
        keyboard = [
            [InlineKeyboardButton("📸 QR Code ဖတ်မယ်", callback_data='read_qr')],
            [InlineKeyboardButton("🎨 QR Code ဖန်တီးမယ်", callback_data='create_qr')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "❌ *မှားနေပါတယ်!*\n\nသင်က *QR Code ဖတ်မယ်* ကို ရွေးထားပါတယ်။ QR Code ပါတဲ့*ဓာတ်ပုံ* တစ်ပုံကို ပို့ပေးပါ။\n\n💡 QR Code ဖန်တီးချင်ရင် အောက်က ခလုတ်ကို နှိပ်ပါ။",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        # No mode selected - ask user to choose
        keyboard = [
            [InlineKeyboardButton("🎨 QR Code ဖန်တီးမယ်", callback_data='create_qr')],
            [InlineKeyboardButton("📸 QR Code ဖတ်မယ်", callback_data='read_qr')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🤔 *ဘာလုပ်ချင်လဲ ရွေးပါ*\n\nအရင်ဆုံး အောက်က ခလုတ်တွေကနေ လုပ်ချင်တဲ့အရာကို ရွေးချယ်ပါ။",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def handle_photo_message(update: Update, context) -> None:
    user_id = update.effective_user.id
    current_state = user_states.get(user_id)
    
    if current_state == 'read_mode':
        # User is in QR reading mode - read QR code
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
                await update.message.reply_text("❌ ဓာတ်ပုံကို ဖတ်လို့မရပါဘူး။ တခြားပုံတစ်ပုံကို ထပ်ပို့ကြည့်ပါ။")
                return

            # Initialize the QRCode detector
            detector = cv2.QRCodeDetector()
            data, vertices, straight_qrcode = detector.detectAndDecode(img)
            
            # Only show "QR Code ဖန်တီးမယ်" button as requested
            keyboard = [
                [InlineKeyboardButton("🎨 QR Code ဖန်တီးမယ်", callback_data='create_qr')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if data:
                reply_text = f"✅ *QR Code ဖတ်ပြီးပါပြီ်*\n\nတွေ့ရှိသော အချက်အလက်:\n`{data}`"
            else:
                reply_text = "❌ *QR Code မတွေ့ပါ*\n\nဒီပုံထဲမှာ QR Code မတွေ့ပါဘူး။ ရှင်းလင်းတဲ့ QR Code ပုံတစ်ပုံကို ထပ်ပို့ကြည့်ပါ။"
            
            await update.message.reply_text(
                reply_text, 
                parse_mode='Markdown', 
                reply_markup=reply_markup,
                reply_to_message_id=update.message.message_id
            )

        except Exception as e:
            logger.error(f"Error decoding QR code with OpenCV: {e}")
            keyboard = [
                [InlineKeyboardButton("📸 QR Code ထပ်ဖတ်မယ်", callback_data='read_qr')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "❌ QR Code ကိုဖတ်ရာတွင် အမှားတစ်ခုဖြစ်ပွားသွားပါတယ်။ ထပ်ကြိုးစားကြည့်ပါ။",
                reply_markup=reply_markup
            )
            
    elif current_state == 'create_mode':
        # User is in QR creation mode but sent photo - show error
        keyboard = [
            [InlineKeyboardButton("🎨 QR Code ဖန်တီးမယ်", callback_data='create_qr')],
            [InlineKeyboardButton("📸 QR Code ဖတ်မယ်", callback_data='read_qr')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "❌ *မှားနေပါတယ်!*\n\nသင်က *QR Code ဖန်တီးမယ်* ကို ရွေးထားပါတယ်။ QR Code ပြုလုပ်လိုတဲ့*စာ* သို့မဟုတ် *Link* ကို ပို့ပေးပါ။\n\n💡 QR Code ဖတ်ချင်ရင် အောက်က ခလုတ်ကို နှိပ်ပါ။",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        # No mode selected - ask user to choose
        keyboard = [
            [InlineKeyboardButton("🎨 QR Code ဖန်တီးမယ်", callback_data='create_qr')],
            [InlineKeyboardButton("📸 QR Code ဖတ်မယ်", callback_data='read_qr')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🤔 *ဘာလုပ်ချင်လဲ ရွေးပါ*\n\nအရင်ဆုံး အောက်က ခလုတ်တွေကနေ လုပ်ချင်တဲ့အရာကို ရွေးချယ်ပါ။",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )


async def handle_other_messages(update: Update, context) -> None:
    user_id = update.effective_user.id
    current_state = user_states.get(user_id)
    
    keyboard = [
        [InlineKeyboardButton("🎨 QR Code ဖန်တီးမယ်", callback_data='create_qr')],
        [InlineKeyboardButton("📸 QR Code ဖတ်မယ်", callback_data='read_qr')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if current_state == 'create_mode':
        await update.message.reply_text(
            "❌ *မှားနေပါတယ်!*\n\nသင်က *QR Code ဖန်တီးမယ်* ကို ရွေးထားပါတယ်။ QR Code ပြုလုပ်လိုတဲ့*စာ* သို့မဟုတ် *Link* ကို ပို့ပေးပါ။",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    elif current_state == 'read_mode':
        await update.message.reply_text(
            "❌ *မှားနေပါတယ်!*\n\nသင်က *QR Code ဖတ်မယ်* ကို ရွေးထားပါတယ်။ QR Code ပါတဲ့*ဓာတ်ပုံ* တစ်ပုံကို ပို့ပေးပါ။",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "🤔 *ဘာလုပ်ချင်လဲ ရွေးပါ*\n\nအရင်ဆုံး အောက်က ခလုတ်တွေကနေ လုပ်ချင်တဲ့အရာကို ရွေးချယ်ပါ။",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )


# --- Callback & Inline Handlers ---
async def button_handler(update: Update, context) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == 'create_qr':
        user_states[user_id] = 'create_mode'
        # Send new message instead of editing to avoid error
        await query.message.reply_text(
            "🎨 *QR Code ဖန်တီးမယ်* ကို ရွေးထားပါတယ်\n\nQR Code ပြုလုပ်လိုတဲ့*စာ* သို့မဟုတ် *Link* ကို ပို့ပေးလိုက်ပါ။\n\n⚠️ *သတိ:* ဓာတ်ပုံ ပို့လို့မရပါဘူးနော်။",
            parse_mode='Markdown'
        )
    elif query.data == 'read_qr':
        user_states[user_id] = 'read_mode'
        # Send new message instead of editing to avoid error
        await query.message.reply_text(
            "📸 *QR Code ဖတ်မယ်* ကို ရွေးထားပါတယ်\n\nQR Code ပါတဲ့*ဓာတ်ပုံ* တစ်ပုံကို ပို့ပေးပါ။\n\n⚠️ *သတိ:* စာ သို့မဟုတ် Link ပို့လို့မရပါဘူးနော်။",
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
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(InlineQueryHandler(inline_qr))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))
    application.add_handler(MessageHandler(~(filters.TEXT | filters.PHOTO | filters.COMMAND), handle_other_messages))

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