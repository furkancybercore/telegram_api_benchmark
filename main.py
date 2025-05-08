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

    # Store results in a dictionary keyed by library name
    benchmark_results_by_library = {}

    for sender in senders_to_test:
        print(f"\n--- Starting benchmark for {sender.library_name} ---")
        result_data = None
        if sender.get_sender_type() == "async":
            try:
                result_data = await sender.run_benchmark_async(config.NUM_MESSAGES, config.TEST_MESSAGE_PAYLOAD)
            except NotImplementedError:
                print(f"{sender.library_name} async benchmark not implemented, skipping.")
            except Exception as e:
                print(f"Error during async benchmark for {sender.library_name}: {e}")
        else:  # sync
            try:
                result_data = sender.run_benchmark(config.NUM_MESSAGES, config.TEST_MESSAGE_PAYLOAD)
            except NotImplementedError:
                print(f"{sender.library_name} sync benchmark not implemented, skipping.")
            except Exception as e:
                print(f"Error during sync benchmark for {sender.library_name}: {e}")
        
        if result_data:
            benchmark_results_by_library[sender.library_name.lower()] = result_data
        
        print(f"--- Finished benchmark for {sender.library_name} ---")

    # Prepare data for reporting
    # Extract library versions for the report details
    lib_versions_for_report = {name: data.get("version", "N/A") 
                               for name, data in benchmark_results_by_library.items()}

    benchmark_data_for_reports = {
        "benchmark_details": {
            "project_name": config.PROJECT_NAME,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "libraries_versions": lib_versions_for_report, # Using extracted versions
            "parameters": {
                "num_messages_per_library": config.NUM_MESSAGES,
                "telegram_api_url": config.TELEGRAM_API_URL_TEMPLATE.format(token="[REDACTED]")
            }
        },
        "libraries": benchmark_results_by_library, # Main results structured by library
        "overall_summary": {}
    }

    # Calculate overall summary based on the new structure
    if benchmark_results_by_library:
        # Filter for libraries that have workflow data and valid avg_telegram_send_time_s
        valid_results_for_summary = [
            (name, lib_data["workflow"])
            for name, lib_data in benchmark_results_by_library.items()
            if "workflow" in lib_data and lib_data["workflow"].get("avg_telegram_send_time_s") is not None and lib_data["workflow"]["avg_telegram_send_time_s"] > 0
        ]

        if valid_results_for_summary:
            # Sort by avg_telegram_send_time_s
            fastest_send_time = min(valid_results_for_summary, key=lambda x: x[1]["avg_telegram_send_time_s"])
            slowest_send_time = max(valid_results_for_summary, key=lambda x: x[1]["avg_telegram_send_time_s"])
            
            # Sort by success_rate_percent
            most_reliable = max(valid_results_for_summary, key=lambda x: x[1]["success_rate_percent"])

            # Filter for resource rankings (where data might be present and non-zero)
            valid_for_memory = [(name, lib_data["workflow"]) for name, lib_data in benchmark_results_by_library.items() if "workflow" in lib_data and lib_data["workflow"].get("memory_increase_mb") is not None]
            valid_for_cpu = [(name, lib_data["workflow"]) for name, lib_data in benchmark_results_by_library.items() if "workflow" in lib_data and lib_data["workflow"].get("cpu_time_percent") is not None]

            lowest_mem_increase = min(valid_for_memory, key=lambda x: x[1]["memory_increase_mb"]) if valid_for_memory else (None, {"memory_increase_mb": 0})
            lowest_cpu_usage = min(valid_for_cpu, key=lambda x: x[1]["cpu_time_percent"]) if valid_for_cpu else (None, {"cpu_time_percent": 0})
            
            overall_summary_content = {
                "fastest_avg_telegram_send_time": fastest_send_time[0],
                "fastest_avg_telegram_send_time_s": fastest_send_time[1]["avg_telegram_send_time_s"],
                "slowest_avg_telegram_send_time": slowest_send_time[0],
                "slowest_avg_telegram_send_time_s": slowest_send_time[1]["avg_telegram_send_time_s"],
                "highest_success_rate_library": most_reliable[0],
                "highest_success_rate_percent": most_reliable[1]["success_rate_percent"],
                "lowest_memory_library": lowest_mem_increase[0],
                "lowest_memory_increase_mb": lowest_mem_increase[1]["memory_increase_mb"],
                "lowest_cpu_library": lowest_cpu_usage[0],
                "lowest_cpu_time_percent": lowest_cpu_usage[1]["cpu_time_percent"],
                "rankings": { 
                    "avg_telegram_send_time": sorted([ (lib_name, data["avg_telegram_send_time_s"]) for lib_name, data in valid_results_for_summary], key=lambda x: x[1]),
                    "success_rate": sorted([ (lib_name, data["success_rate_percent"]) for lib_name, data in valid_results_for_summary], key=lambda x: x[1], reverse=True),
                    "memory_usage": sorted([ (name, data["memory_increase_mb"]) for name, data in valid_for_memory], key=lambda x: x[1]) if valid_for_memory else [],
                    "cpu_usage": sorted([ (name, data["cpu_time_percent"]) for name, data in valid_for_cpu], key=lambda x: x[1]) if valid_for_cpu else []
                }
            }
            benchmark_data_for_reports["overall_summary"] = overall_summary_content

    # Generate reports
    json_reporter.generate_report(benchmark_data_for_reports, config.REPORTS_DIR, config.JSON_REPORT_FILENAME)
    md_reporter.generate_report(benchmark_data_for_reports, config.REPORTS_DIR, config.MD_REPORT_FILENAME)
    
    end_script_time = time.perf_counter()
    print(f"\nBenchmark finished in {end_script_time - start_script_time:.2f} seconds.")
    print(f"Reports generated in '{config.REPORTS_DIR}' directory.")

if __name__ == "__main__":
    asyncio.run(main()) 