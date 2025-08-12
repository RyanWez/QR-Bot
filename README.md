# QR MM Bot 🤖

Myanmar QR Code Generator and Reader Telegram Bot

## Features ✨

- 🎨 **QR Code Generation**: Create QR codes from text or links
- 📸 **QR Code Reading**: Read QR codes from images using OpenCV
- 🇲🇲 **Myanmar Language**: Full Myanmar language support
- 🔄 **Smart Mode Switching**: Separate modes for creation and reading
- ⚡ **Fast Processing**: Optimized QR code generation and reading

## Setup 🚀

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd QR-MM
```

### 2. Create virtual environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file and add your bot token
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
BOT_NAME=QR MM Bot
BOT_USERNAME=your_bot_username
```

### 5. Get Telegram Bot Token
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Create a new bot with `/newbot`
3. Copy the token and paste it in your `.env` file

### 6. Run the bot
```bash
python qrmm.py
```

## Usage 📱

1. Start the bot with `/start`
2. Choose your action:
   - **🎨 QR Code ဖန်တီးမယ်**: Send text or link to generate QR code
   - **📸 QR Code ဖတ်မယ်**: Send image to read QR code

## Dependencies 📦

- `python-telegram-bot` - Telegram Bot API
- `qrcode[pil]` - QR code generation
- `opencv-python-headless` - Image processing for QR reading
- `numpy` - Numerical operations
- `python-dotenv` - Environment variable management

## Project Structure 📁

```
QR-MM/
├── qrmm.py              # Main bot application
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not in git)
├── .env.example        # Environment template
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Error Handling 🛠️

The bot includes comprehensive error handling for:
- Network timeouts
- Invalid QR codes
- Image processing errors
- API rate limits

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License 📄

This project is open source and available under the [MIT License](LICENSE).

## Support 💬

If you encounter any issues, please create an issue on GitHub or contact the maintainer.

---

Made with ❤️ for Myanmar developers