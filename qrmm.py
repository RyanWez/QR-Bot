import logging
import qrcode
import io
import uuid
import os
from urllib.parse import quote
from dotenv import load_dotenv

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

# Validate required environment variables
if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
    raise ValueError("TELEGRAM_BOT_TOKEN is required. Please check your .env file.")

# User states
user_states = {}

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
    *3. Inline Mode*
    - ဘယ် chat ထဲမှာမဆို `@qrmmbot` လို့ ရိုက်ထည့်ပြီး ခေါ်သုံးနိုင်ပါတယ်။

    - Source Code ရယူရန်=> @RyanWez
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')


# --- Message Handlers ---
async def handle_text_message(update: Update, context) -> None:
    user_id = update.effective_user.id
    text = update.message.text
    
    # Check user state
    current_state = user_states.get(user_id)
    
    if current_state == 'create_mode':
        # User is in QR creation mode - generate QR code
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        try:
            # Generate QR code with optimized settings
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(text)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            bio = io.BytesIO()
            bio.name = 'qr_code.png'
            qr_img.save(bio, 'PNG', optimize=True)
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
                    caption=f"✅ *QR Code ဖန်တီးပြီးပါပြီ်*\n\nစာ: `{text}` အတွက် QR Code ပါ",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
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
                    f"✅ *QR Code ဖန်တီးပြီးပါပြီ်*\n\nစာ: `{text}` အတွက် QR Code ပါ\n\n⚠️ ဓာတ်ပုံ ပို့ရာတွင် ပြဿနာရှိနေပါတယ်။ Network connection ကို စစ်ကြည့်ပါ။",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
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
            
            await update.message.reply_text(reply_text, parse_mode='Markdown', reply_markup=reply_markup)

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


def main() -> None:
    # Build application with timeout settings
    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .build()
    )
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(InlineQueryHandler(inline_qr))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))
    application.add_handler(MessageHandler(~(filters.TEXT | filters.PHOTO | filters.COMMAND), handle_other_messages))
    print("Bot is running...")
    application.run_polling()


if __name__ == '__main__':
    main()