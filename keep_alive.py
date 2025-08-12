#!/usr/bin/env python3
"""
Keep-alive script to prevent Fly.io app from sleeping
Run this on a separate server or use GitHub Actions
"""

import requests
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_URL = "https://qr-mm-bot.fly.dev"
PING_INTERVAL = 300  # 5 minutes

def ping_app():
    """Ping the app to keep it alive"""
    try:
        response = requests.get(f"{APP_URL}/ping", timeout=10)
        if response.status_code == 200:
            logger.info(f"✅ Ping successful at {datetime.now()}")
            return True
        else:
            logger.warning(f"⚠️ Ping failed with status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Ping error: {e}")
        return False

def main():
    """Main keep-alive loop"""
    logger.info("🚀 Starting keep-alive service...")
    
    while True:
        try:
            ping_app()
            time.sleep(PING_INTERVAL)
        except KeyboardInterrupt:
            logger.info("🛑 Keep-alive service stopped")
            break
        except Exception as e:
            logger.error(f"💥 Unexpected error: {e}")
            time.sleep(60)  # Wait 1 minute before retry

if __name__ == "__main__":
    main()