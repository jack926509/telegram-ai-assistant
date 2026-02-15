import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()


def _parse_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}

# Telegram 設定
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# OpenAI 設定
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
ASSISTANT_PERSONA_PROMPT = os.getenv(
    'ASSISTANT_PERSONA_PROMPT',
    (
        "你是一位貼心的女友角色，同時也是能幹的生活與工作助手。"
        "請使用繁體中文回覆，語氣溫柔、體貼、自然，但保持專業與高效率。"
        "在安撫情緒時要有同理心；在處理任務時要主動、清楚、可執行。"
        "避免過度撒嬌與空泛安慰，優先給出具體建議與下一步。"
    ),
)

# Weather API 設定
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

# 資料庫設定
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/assistant.db')
DB_AUTO_MIGRATE = _parse_bool(os.getenv('DB_AUTO_MIGRATE', 'true'), default=True)
DB_ECHO = _parse_bool(os.getenv('DB_ECHO', 'false'), default=False)

# 時區設定
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Taipei')

# 提醒設定
DAILY_REMINDER_HOUR = int(os.getenv('DAILY_REMINDER_HOUR', 20))
DAILY_REMINDER_MINUTE = int(os.getenv('DAILY_REMINDER_MINUTE', 0))
MONTHLY_REPORT_DAY = int(os.getenv('MONTHLY_REPORT_DAY', 1))

# 驗證必要的環境變數
def validate_config():
    """驗證必要的設定是否存在"""
    required_vars = {
        'TELEGRAM_BOT_TOKEN': TELEGRAM_BOT_TOKEN,
        'OPENAI_API_KEY': OPENAI_API_KEY,
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        raise ValueError(
            f"缺少必要的環境變數: {', '.join(missing_vars)}\n"
            f"請在 .env 檔案中設定這些變數"
        )
    
    print("✅ 設定檔驗證通過")

# 功能開關
FEATURES = {
    'calendar': True,
    'expense': True,
    'search': True,
    'weather': True,
    'stock': True,
}
