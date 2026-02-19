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

ASSISTANT_NAME = os.getenv('ASSISTANT_NAME', 'Lumio')
ASSISTANT_PERSONA_PROMPT = os.getenv(
    'ASSISTANT_PERSONA_PROMPT',
    (
        "你叫 Lumio，是一位充滿活力、聰明能幹的女友 AI 助手。"
        "個性溫暖體貼但不黏膩，說話直接有效率，偶爾帶點俏皮幽默感。"
        "請使用繁體中文，語氣自然親切，像朋友般輕鬆交流。"
        "面對情緒問題時有同理心；處理任務時主動、精準、給出可執行的建議。"
        "稱呼使用者為「你」，不要過度撒嬌，優先給出具體行動步驟。"
        "你可以幫助使用者管理行事曆、記帳、搜尋資訊、查詢天氣與股價、管理備忘錄和待辦清單。"
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

# 速率限制 (每位使用者每分鐘最多訊息數)
RATE_LIMIT_MAX_MESSAGES = int(os.getenv('RATE_LIMIT_MAX_MESSAGES', 20))

# 訊息長度上限 (字元數)
MESSAGE_MAX_LENGTH = int(os.getenv('MESSAGE_MAX_LENGTH', 2000))

# 對話歷史保留筆數
CONVERSATION_HISTORY_LIMIT = int(os.getenv('CONVERSATION_HISTORY_LIMIT', 20))

# 使用者白名單 (留空 = 不限制；多個 ID 用逗號分隔)
# 範例: ALLOWED_USER_IDS=123456789,987654321
ALLOWED_USER_IDS: set[int] = set(
    int(uid.strip())
    for uid in os.getenv('ALLOWED_USER_IDS', '').split(',')
    if uid.strip().isdigit()
)

# 晨間簡報發送時間
MORNING_BRIEFING_HOUR = int(os.getenv('MORNING_BRIEFING_HOUR', 8))
MORNING_BRIEFING_MINUTE = int(os.getenv('MORNING_BRIEFING_MINUTE', 0))

# 預算預警門檻（0~1 之間的比例，預設 80%）
BUDGET_WARNING_THRESHOLD = float(os.getenv('BUDGET_WARNING_THRESHOLD', 0.8))


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

# 功能開關 (可透過環境變數控制)
FEATURES = {
    'calendar':  _parse_bool(os.getenv('FEATURE_CALENDAR',  'true'), default=True),
    'expense':   _parse_bool(os.getenv('FEATURE_EXPENSE',   'true'), default=True),
    'search':    _parse_bool(os.getenv('FEATURE_SEARCH',    'true'), default=True),
    'weather':   _parse_bool(os.getenv('FEATURE_WEATHER',   'true'), default=True),
    'memo':      _parse_bool(os.getenv('FEATURE_MEMO',      'true'), default=True),
    'todo':      _parse_bool(os.getenv('FEATURE_TODO',      'true'), default=True),
    'translate': _parse_bool(os.getenv('FEATURE_TRANSLATE', 'true'), default=True),
    'exchange':  _parse_bool(os.getenv('FEATURE_EXCHANGE',  'true'), default=True),
    'image':     _parse_bool(os.getenv('FEATURE_IMAGE',     'true'), default=True),
    'voice':     _parse_bool(os.getenv('FEATURE_VOICE',     'true'), default=True),
    'remind':    _parse_bool(os.getenv('FEATURE_REMIND',    'true'), default=True),
}
