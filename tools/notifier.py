# tools/notifier.py

import os
import httpx
from dotenv import load_dotenv

# Load env variables
load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_notification(message: str, notification_type: str = "info"):
    """
    Dispatches a message payload to configured Discord or Telegram channels.
    Supports basic markdown styling and embeds indicators based on severity.
    """
    # Build a visual header based on notification type
    emoji = "ℹ️"
    if notification_type == "success":
        emoji = "✅"
    elif notification_type == "warning" or notification_type == "review":
        emoji = "⏳"
    elif notification_type == "error":
        emoji = "❌"
        
    formatted_msg = f"{emoji} **[AI Career Assistant]**\n{message}"
    
    # 1. Discord Dispatch
    if DISCORD_WEBHOOK_URL:
        try:
            # Color representation: Green=65280, Gray=8421504, Orange=16753920, Red=16711680
            color = 8421504
            if notification_type == "success":
                color = 65280
            elif notification_type == "warning" or notification_type == "review":
                color = 16753920
            elif notification_type == "error":
                color = 16711680
                
            payload = {
                "embeds": [{
                    "description": message,
                    "title": f"{emoji} AI Career Assistant Update",
                    "color": color
                }]
            }
            response = httpx.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10.0)
            if response.status_code >= 400:
                print(f"[Notifier Error] Discord returned status code {response.status_code}: {response.text}")
        except Exception as e:
            print(f"[Notifier Error] Failed to send Discord alert: {e}")
            
    # 2. Telegram Dispatch
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            
            # Escape HTML characters in the raw message to prevent parsing errors
            import html
            import re
            escaped_msg = html.escape(message)
            
            # Format markdown tags to HTML tags correctly using regular expressions
            escaped_msg = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', escaped_msg)
            escaped_msg = re.sub(r'\*(.*?)\*', r'<i>\1</i>', escaped_msg)
            escaped_msg = re.sub(r'`(.*?)`', r'<code>\1</code>', escaped_msg)
            
            cleaned_message = f"{emoji} <b>[AI Career Assistant]</b>\n{escaped_msg}"
            
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": cleaned_message,
                "parse_mode": "HTML"
            }
            response = httpx.post(url, json=payload, timeout=10.0)
            if response.status_code >= 400:
                print(f"[Notifier Error] Telegram returned status code {response.status_code}: {response.text}")
        except Exception as e:
            print(f"[Notifier Error] Failed to send Telegram alert: {e}")
            
    # Always log to console as fallback
    print(f"[Notification - {notification_type.upper()}] {message}")
