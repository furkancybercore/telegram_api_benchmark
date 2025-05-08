import os
from dotenv import load_dotenv

load_dotenv() # Load variables from .env file

# --- Telegram API Configuration ---
# Fallback to placeholders if not set in environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', 'YOUR_TELEGRAM_CHAT_ID')

if TELEGRAM_BOT_TOKEN == 'YOUR_TELEGRAM_BOT_TOKEN' or TELEGRAM_CHAT_ID == 'YOUR_TELEGRAM_CHAT_ID':
    print("WARNING: Telegram Bot Token or Chat ID is not set. Please create a .env file with TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID or update config.py.")

TELEGRAM_API_URL_TEMPLATE = "https://api.telegram.org/bot{token}/sendMessage"

# --- Benchmark Parameters ---
NUM_MESSAGES = 5  # Number of messages to send for each library
TEST_MESSAGE_PAYLOAD = "Hello from the Telegram Benchmark Script!"

# --- Report Configuration ---
REPORTS_DIR = "reports"
JSON_REPORT_FILENAME = "benchmark_telegram_libs.json"
MD_REPORT_FILENAME = "benchmark_telegram_libs_report.md"

# --- Project Details (for reporting) ---
PROJECT_NAME = "Telegram HTTP Library Benchmark"

# --- Database Configuration (PostgreSQL) ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "telegramtestdb")
DB_USER = os.getenv("DB_USER", "furkan")
DB_PASSWORD = os.getenv("DB_PASSWORD", "0000")

DATABASE_URL_SYNC = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DATABASE_URL_ASYNC = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}" # asyncpg uses the same format prefix

# Check if default DB credentials are used and warn
if DB_USER == 'furkan' and DB_PASSWORD == '0000' and DB_HOST == 'localhost':
    print("WARNING: Using default PostgreSQL credentials from config.py. Consider setting DB_HOST, DB_PORT, DB_NAME, DB_USER, and DB_PASSWORD environment variables.")

DB_TABLE_NAME = "messages_to_send"
DB_SETUP_WAIT_SECONDS = 2 # Seconds to wait after setup before benchmarks 