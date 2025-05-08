# Telegram HTTP Library Benchmark

This project benchmarks various Python HTTP libraries for sending messages to the Telegram API.
It measures performance metrics like request time and success rate, and generates JSON and Markdown reports.

## Features

- Benchmarks the following libraries:
    - `httpx` (asynchronous)
    - `aiohttp` (asynchronous)
    - `requests` (synchronous)
    - `urllib3` (synchronous)
- Sends a configurable number of messages (default: 10) using each library.
- Collects individual request times, success/failure status.
- Calculates summary statistics (total time, average, min, max times, success rate).
- Generates a detailed JSON report.
- Generates a summary Markdown report.

## Setup

1.  **Clone the repository (or create the project files as provided).**

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Telegram API credentials:**
    Create a `.env` file in the `telegram_api_benchmark` directory by copying `.env.example` (or creating it manually):
    ```
    TELEGRAM_BOT_TOKEN=YOUR_ACTUAL_BOT_TOKEN_HERE
    TELEGRAM_CHAT_ID=YOUR_ACTUAL_CHAT_ID_HERE
    ```
    Replace the placeholder values with your actual Telegram Bot Token and Chat ID.
    Alternatively, you can modify the `config.py` file directly, but using a `.env` file is more secure for sensitive credentials.

## Usage

Run the main benchmark script from the `telegram_api_benchmark` directory:

```bash
python main.py
```

This will execute the benchmarks and generate the following files in a `reports` subdirectory (created if it doesn't exist):
- `benchmark_telegram_libs.json`: Detailed JSON report.
- `benchmark_telegram_libs_report.md`: Summary Markdown report.

## Report Structure

### JSON Report (`benchmark_telegram_libs.json`)
Contains detailed information about the benchmark run, including:
- Benchmark metadata (project name, timestamp, Python version, library versions, parameters).
- Results for each library:
    - List of individual attempt details (status, response time, success).
    - Summary statistics (total time, average time, success/failure counts).
- Overall summary comparing libraries.

### Markdown Report (`benchmark_telegram_libs_report.md`)
Provides a human-readable summary of the benchmark results, including:
- Introduction
- Methodology
- Key Findings (comparison table)
- Individual Library Performance
- Conclusion

This report is designed to be similar in spirit to the example reports you provided.

## Note on CPU/Memory Profiling

The current version focuses on timing and success rates for API calls. Detailed CPU and memory profiling for each specific library's execution block can be complex to implement accurately without external tools or more intricate `psutil` integration. The report structure includes placeholders for these, and they can be added as a future enhancement if precise, isolated measurements are required. 