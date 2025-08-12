#!/bin/bash

# QR MM Bot Deployment Script for Fly.io

echo "🚀 Deploying QR MM Bot to Fly.io..."

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl is not installed. Please install it first:"
    echo "   curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Check if user is logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "🔐 Please login to Fly.io first:"
    echo "   flyctl auth login"
    exit 1
fi

# Check if app exists
if ! flyctl apps list | grep -q "qr-mm-bot"; then
    echo "📱 Creating new Fly.io app..."
    flyctl apps create qr-mm-bot --org personal
fi

# Set secrets
echo "🔑 Setting up secrets..."
read -p "Enter your Telegram Bot Token: " BOT_TOKEN
flyctl secrets set TELEGRAM_BOT_TOKEN="$BOT_TOKEN"
flyctl secrets set WEBHOOK_URL="https://qr-mm-bot.fly.dev"
flyctl secrets set BOT_NAME="QR MM Bot"
flyctl secrets set BOT_USERNAME="qrmmbot"

# Deploy the app
echo "🚀 Deploying application..."
flyctl deploy

# Check deployment status
echo "✅ Deployment completed!"
echo "🌐 Your bot is now available at: https://qr-mm-bot.fly.dev"
echo "📊 Check status: flyctl status"
echo "📋 View logs: flyctl logs"

echo ""
echo "🎉 QR MM Bot has been successfully deployed to Fly.io!"
echo "💡 Don't forget to test your bot on Telegram!"