import asyncio
import datetime
import platform
import time # For overall script timing

# Project specific imports
import config
from senders.httpx_sender import HttpxSender
from senders.aiohttp_sender import AiohttpSender
from senders.requests_sender import RequestsSender
from senders.urllib3_sender import Urllib3Sender
from reporting import json_reporter, md_reporter

async def main():
    start_script_time = time.perf_counter()
    print(f"Starting {config.PROJECT_NAME}...")

    if config.TELEGRAM_BOT_TOKEN == 'YOUR_TELEGRAM_BOT_TOKEN' or \
       config.TELEGRAM_CHAT_ID == 'YOUR_TELEGRAM_CHAT_ID':
        print("ERROR: Please configure your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file or config.py before running.")
        return

    # Initialize senders
    senders_to_test = [
        HttpxSender(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, config.TELEGRAM_API_URL_TEMPLATE),
        AiohttpSender(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, config.TELEGRAM_API_URL_TEMPLATE),
        RequestsSender(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, config.TELEGRAM_API_URL_TEMPLATE),
        Urllib3Sender(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, config.TELEGRAM_API_URL_TEMPLATE),
    ]

    all_results = []
    library_versions = {}

    for sender in senders_to_test:
        print(f"\n--- Starting benchmark for {sender.library_name} ---")
        if sender.get_sender_type() == "async":
            try:
                result = await sender.run_benchmark_async(config.NUM_MESSAGES, config.TEST_MESSAGE_PAYLOAD)
                all_results.append(result)
            except NotImplementedError:
                print(f"{sender.library_name} async benchmark not implemented, skipping.")
            except Exception as e:
                print(f"Error during async benchmark for {sender.library_name}: {e}")
                # Optionally add a failed result structure
        else: # sync
            try:
                result = sender.run_benchmark(config.NUM_MESSAGES, config.TEST_MESSAGE_PAYLOAD)
                all_results.append(result)
            except NotImplementedError:
                print(f"{sender.library_name} sync benchmark not implemented, skipping.")
            except Exception as e:
                print(f"Error during sync benchmark for {sender.library_name}: {e}")
        library_versions[sender.library_name.lower()] = sender.get_library_version()
        print(f"--- Finished benchmark for {sender.library_name} ---")

    # Prepare data for reporting
    benchmark_data = {
        "benchmark_details": {
            "project_name": config.PROJECT_NAME,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "libraries_versions": library_versions,
            "parameters": {
                "num_messages": config.NUM_MESSAGES,
                "telegram_api_url": config.TELEGRAM_API_URL_TEMPLATE.format(token="[REDACTED]")
            }
        },
        "results": all_results,
        "overall_summary": {}
    }

    # Calculate overall summary
    if all_results:
        valid_results = [r for r in all_results if r.get('summary', {}).get('average_time_ms') is not None and r.get('summary', {}).get('average_time_ms') > 0]
        if valid_results:
            fastest = min(valid_results, key=lambda x: x['summary']['average_time_ms'])
            slowest = max(valid_results, key=lambda x: x['summary']['average_time_ms'])
            most_reliable = max(valid_results, key=lambda x: x['summary']['success_rate_percent'])
            
            benchmark_data["overall_summary"] = {
                "fastest_library_avg_time": f"{fastest['library']} ({fastest['type']})",
                "fastest_avg_time_ms": fastest['summary']['average_time_ms'],
                "slowest_library_avg_time": f"{slowest['library']} ({slowest['type']})",
                "slowest_avg_time_ms": slowest['summary']['average_time_ms'],
                "most_reliable_library": f"{most_reliable['library']} ({most_reliable['type']})",
                "highest_success_rate": most_reliable['summary']['success_rate_percent'],
                "cpu_usage_comparison": {},
                "memory_usage_comparison": {}
            }

    # Generate reports
    json_reporter.generate_report(benchmark_data, config.REPORTS_DIR, config.JSON_REPORT_FILENAME)
    md_reporter.generate_report(benchmark_data, config.REPORTS_DIR, config.MD_REPORT_FILENAME)
    
    end_script_time = time.perf_counter()
    print(f"\nBenchmark finished in {end_script_time - start_script_time:.2f} seconds.")
    print(f"Reports generated in '{config.REPORTS_DIR}' directory.")

if __name__ == "__main__":
    asyncio.run(main()) 