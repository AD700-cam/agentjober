# scratch/test_telegram.py

import os
import sys
import httpx
from dotenv import load_dotenv

# Ensure project root in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

load_dotenv()

def test_telegram():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    print("=========================================")
    print("📡 Telegram Integration Diagnostic Tool")
    print("=========================================")
    print(f"Token Configured: {'Yes' if token else 'No'}")
    if token:
        print(f"Token (First/Last 4): {token[:4]}...{token[-4:] if len(token) > 4 else ''}")
    print(f"Chat ID Configured: {'Yes' if chat_id else 'No'}")
    if chat_id:
        print(f"Chat ID: {chat_id}")
    print("=========================================\n")
    
    if not token or not chat_id:
        print("❌ Error: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in .env file.")
        print("Please copy .env.example to .env and configure them.")
        return
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "🎯 <b>AI Career Assistant:</b> Connection test successful!",
        "parse_mode": "HTML"
    }
    
    print("📤 Dispatching diagnostic message to Telegram API...")
    try:
        response = httpx.post(url, json=payload, timeout=10.0)
        print(f"📥 Status Code: {response.status_code}")
        print(f"📥 Response Body: {response.text}")
        if response.status_code == 200:
            print("\n✅ Success! Telegram bot successfully received and dispatched the message.")
        else:
            print("\n❌ Failed! The Telegram API rejected the request. Please check the error details above.")
    except Exception as e:
        print(f"\n❌ Error: Connection failed: {e}")

if __name__ == "__main__":
    test_telegram()
