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
NUM_MESSAGES = 2  # Number of messages to send for each library
TEST_MESSAGE_PAYLOAD = "Hello from the Telegram Benchmark Script!"

# --- Report Configuration ---
REPORTS_DIR = "reports"
JSON_REPORT_FILENAME = "benchmark_telegram_libs.json"
MD_REPORT_FILENAME = "benchmark_telegram_libs_report.md"

# --- Project Details (for reporting) ---
PROJECT_NAME = "Telegram HTTP Library Benchmark" 