"""Script to validate configuration"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app.core.config import settings
    
    print("✓ Configuration loaded successfully!")
    print(f"\nApp Name: {settings.app_name}")
    print(f"App Version: {settings.app_version}")
    print(f"Database URL: {settings.database_url}")
    print(f"Log Level: {settings.log_level}")
    print(f"SerpApi Timeout: {settings.serpapi_timeout}s")
    print(f"\n✓ SerpApi API Key: {'*' * 20} (configured)")
    print(f"✓ Telegram Bot Token: {'*' * 20} (configured)")
    print(f"✓ Telegram Chat ID: {settings.telegram_chat_id}")
    
    print("\n✓ All required configuration is present!")
    sys.exit(0)
    
except Exception as e:
    print(f"✗ Configuration error: {e}")
    print("\nPlease ensure:")
    print("1. .env file exists in the project root")
    print("2. All required variables are set:")
    print("   - SERPAPI_API_KEY")
    print("   - TELEGRAM_BOT_TOKEN")
    print("   - TELEGRAM_CHAT_ID")
    print("\nSee .env.example for reference.")
    sys.exit(1)
