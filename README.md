# Telegram HTTP & SDK Benchmark for Telegram API

This project benchmarks various Python HTTP client libraries and SDKs for sending messages to the Telegram API.
It measures performance metrics like request times, success rates, throughput, resource usage (CPU/RAM), and database interaction times. It then generates JSON and Markdown reports, including plots.

## Features

- Benchmarks the following libraries:
    - `httpx` (asynchronous)
    - `aiohttp` (asynchronous)
    - `requests` (synchronous)
    - `urllib3` (synchronous)
    - `uplink` (asynchronous)
    - `python-telegram-bot` (asynchronous, SDK)
    - `pyTelegramBotAPI` (asynchronous, SDK)
- Sends a configurable number of messages (default: 10 per library).
- **NEW:** Reads message content from a PostgreSQL database before sending.
- Collects individual attempt details:
    - Status code and success/failure.
    - Database read time.
    - HTTP request time.
    - Total processing time.
    - Response size.
- Calculates summary statistics:
    - Average, P95, P99, and standard deviation for DB read, HTTP send, and total processing times.
    - Throughput (messages per second).
    - Success rate.
    - Average response size.
- **NEW:** Monitors and reports CPU and RAM usage for each library's benchmark run using `psutil`.
- Generates a detailed JSON report.
- Generates a summary Markdown report with plots for key metrics.

## Setup

1.  **Clone the repository (or create the project files as provided).**

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Linux/macOS:
    source venv/bin/activate
    # On Windows:
    .\venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up PostgreSQL Database:**
    - Ensure you have PostgreSQL installed and running.
    - Create a database and a user for the benchmark. Example `psql` commands:
      ```sql
      CREATE DATABASE telegramtestdb;
      CREATE USER furkan WITH PASSWORD '0000';
      ALTER DATABASE telegramtestdb OWNER TO furkan;
      GRANT ALL PRIVILEGES ON DATABASE telegramtestdb TO furkan;
      ```
    - The script will automatically create the necessary table (`messages_to_send`) and populate it.

5.  **Configure API credentials and Database connection:**
    Create a `.env` file in the `telegram_api_benchmark` directory (you can copy `.env.example` if it exists, or create one manually).
    Populate it with your details:
    ```env
    TELEGRAM_BOT_TOKEN=YOUR_ACTUAL_BOT_TOKEN_HERE
    TELEGRAM_CHAT_ID=YOUR_ACTUAL_CHAT_ID_HERE

    # Optional: Override default benchmark parameters
    # NUM_MESSAGES=20
    # MAX_CONCURRENT_REQUESTS_PER_LIBRARY=50 # For async libraries like aiohttp

    # Database Configuration (update if different from defaults in config.py)
    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=telegramtestdb
    DB_USER=furkan
    DB_PASSWORD=0000
    ```
    Replace placeholder values. Alternatively, modify `config.py`, but `.env` is recommended.

## Usage

Run the main benchmark script from the `telegram_api_benchmark` directory:

```bash
python main.py
```

This will:
1. Connect to the database (and set it up on the first run or if the table is empty).
2. Execute the benchmarks for the selected libraries.
3. Generate reports in the `benchmark_reports` subdirectory (created if it doesn't exist):
    - `benchmark_report.json`: Detailed JSON report.
    - `benchmark_telegram_libs_report.md`: Summary Markdown report with plots.

## Sample Message Sending Code

This section shows a concise example of how each library is used to send a message to the Telegram API within this benchmark. `api_url`, `data`, `text_payload`, etc., are assumed to be defined elsewhere in the respective sender classes.

### `aiohttp` (asynchronous)
```python
# From aiohttp_sender.py
async def send_message_async(self, session: aiohttp.ClientSession, db_conn, text_payload, message_params):
    # api_url and data are constructed here
    async with session.post(api_url, data=data) as response:
        response_body = await response.read()
        # ...
```

### `httpx` (asynchronous)
```python
# From httpx_sender.py
async def send_message_async(self, session: httpx.AsyncClient, db_conn, text_payload, message_params):
    # api_url and data are constructed here
    response = await session.post(api_url, data=data) # Timeout is set on client
    response.raise_for_status()
    # ...
```

### `httpx` (synchronous)
```python
# From httpx_sender.py
def send_message_sync(self, db_conn, text_payload, message_params):
    # api_url and data are constructed here
    with httpx.Client() as client:
        response = client.post(api_url, data=data, timeout=10.0)
        response.raise_for_status()
        # ...
```

### `requests` (synchronous)
```python
# From requests_sender.py
def send_message_sync(self, db_conn, text_payload, message_params):
    # self.api_url and data are constructed here
    response = requests.post(self.api_url, data=data, timeout=10)
    response.raise_for_status()
    # ...
```

### `urllib3` (synchronous)
```python
# From urllib3_sender.py
def send_message_sync(self, db_conn, text_payload, message_params):
    # self.api_url and data are constructed here
    response = self.http.request(
        "POST",
        self.api_url,
        fields=data, # Encodes as multipart/form-data
        timeout=urllib3.Timeout(total=10.0)
    )
    # ...
```

### `python-telegram-bot` (asynchronous SDK)
```python
# From ptb_sender.py
async def send_message_async(self,
                             session: Bot, # Bot is telegram.Bot
                             db_conn,
                             text_payload: str,
                             message_params: dict):
    # self._bot is an initialized telegram.Bot instance
    # api_payload_text is derived from text_payload
    sent_message = await self._bot.send_message(chat_id=self.chat_id, text=api_payload_text)
    # ...
```

### `pyTelegramBotAPI` (asynchronous SDK)
```python
# From pytelegrambotapi_sender.py
async def send_message_async(self,
                             session: AsyncTeleBot, # AsyncTeleBot is telebot.async_telebot.AsyncTeleBot
                             db_conn,
                             text_payload: str,
                             message_params: dict):
    # self._bot is an initialized telebot.async_telebot.AsyncTeleBot instance
    # api_payload_text is derived from text_payload
    sent_message_obj = await self._bot.send_message(chat_id=self.chat_id, text=api_payload_text)
    # ...
```

### `uplink` (asynchronous)
```python
# From uplink_sender.py
async def send_message_async(self,
                           session, # aiohttp.ClientSession
                           db_conn,
                           text_payload,
                           message_params):
    # self._api is an initialized Uplink consumer instance for TelegramAPI
    response = await self._api.send_message(
        chat_id=self.chat_id,
        text=text_payload
    )
    # ...
```

### `uplink` (synchronous)
```python
# From uplink_sender.py
def send_message_sync(self, db_conn, text_payload, message_params):
    import requests
    # url (with token) and data (with chat_id, text_payload) are prepared
    response = requests.post(url, data=data, timeout=10)
    # ...
```

## Report Structure

### JSON Report (`benchmark_report.json`)
Contains detailed information about the benchmark run, including:
- Benchmark metadata (project name, timestamp, Python version, platform, library versions, parameters including DB info).
- Results for each library:
    - `run_details`: List of individual attempt details (status code, response snippet, response size, DB read time, HTTP request time, total processing time, success, error message).
    - `workflow`: Summary statistics including:
        - Average, P95, P99, and standard deviation for DB read, HTTP send, and total processing times (in seconds).
        - Average response size (bytes).
        - Throughput (messages/sec).
        - Total benchmark duration for the library.
        - Success/failure counts and success rate.
        - CPU time percentage and memory increase (MB).
- `overall_summary`: Comparison of libraries, identifying top performers for various metrics and ranked lists.

### Markdown Report (`benchmark_telegram_libs_report.md`)
Provides a human-readable summary of the benchmark results, including:
- Introduction and Methodology.
- System Information and Benchmark Parameters.
- Overall Summary and Rankings (fastest, highest throughput, most reliable, lowest resource usage).
- **Key Performance Indicators (KPIs) with plots:**
    - Success Rate (%)
    - Throughput (Messages/Second)
    - Average Total Processing Time (s) (DB + HTTP)
    - P95 Total Processing Time (s)
    - P99 Total Processing Time (s)
    - Standard Deviation of Total Processing Time (s)
    - Average DB Read Time (s)
    - Average HTTP Send Time (s)
    - Average Response Size (Bytes)
    - CPU Usage (%)
    - Memory Increase (MB)
- KPI Descriptions and what they signify (e.g., "Lower is Better" or "Higher is Better").
- Conclusion.

This report format aims to provide a comprehensive overview for comparing library performance.

## Note on CPU/Memory Profiling

The current version focuses on timing and success rates for API calls. Detailed CPU and memory profiling for each specific library's execution block can be complex to implement accurately without external tools or more intricate `psutil` integration. The report structure includes placeholders for these, and they can be added as a future enhancement if precise, isolated measurements are required. 