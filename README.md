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

This project is open source and available under the [MIT License](https://github.com/RyanWez/QR-Code?tab=MIT-1-ov-file#).

## Deployment to Fly.io 🚀

### Prerequisites
1. Install [Fly.io CLI](https://fly.io/docs/hands-on/install-flyctl/)
2. Create a Fly.io account and login: `flyctl auth login`

### Deployment Steps

#### 1. Create Fly.io App
```bash
flyctl apps create qr-mm-bot --org personal
```

#### 2. Set Environment Variables
```bash
flyctl secrets set TELEGRAM_BOT_TOKEN="your_bot_token_here"
flyctl secrets set WEBHOOK_URL="https://qr-mm-bot.fly.dev"
flyctl secrets set BOT_NAME="QR MM Bot"
flyctl secrets set BOT_USERNAME="your_bot_username"
```

#### 3. Deploy
```bash
flyctl deploy
```

#### 4. Monitor
```bash
# Check status
flyctl status

# View logs
flyctl logs

# Scale if needed
flyctl scale count 1
```

### Production Environment Variables

When deploying to Fly.io, make sure these environment variables are set:

- `TELEGRAM_BOT_TOKEN` - Your bot token from BotFather
- `WEBHOOK_URL` - Your Fly.io app URL (e.g., https://qr-mm-bot.fly.dev)
- `PORT` - Port number (automatically set by Fly.io to 8080)
- `HOST` - Host address (automatically set to 0.0.0.0)

### Automatic Deployment Script

For easier deployment, you can use the provided script:

```bash
# Linux/Mac
./deploy.sh

# Windows
bash deploy.sh
```

## Architecture 🏗️

### Development Mode
- Uses **polling** to get updates from Telegram
- Runs locally on your machine
- Good for testing and development

### Production Mode (Fly.io)
- Uses **webhooks** for better performance
- Includes health check endpoint at `/health`
- Auto-scaling and auto-sleep capabilities
- Optimized Docker container

## Support 💬

If you encounter any issues, please create an issue on GitHub or contact the maintainer.

---

Made with ❤️ for Myanmar developers