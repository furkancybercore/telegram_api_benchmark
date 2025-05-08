import asyncio
import datetime
import platform
import time
import sys # For error handling

# Project specific imports
import config
from senders.httpx_sender import HttpxSender
from senders.aiohttp_sender import AiohttpSender
from senders.requests_sender import RequestsSender
from senders.urllib3_sender import Urllib3Sender
from senders.uplink_sender import UplinkSender
from senders.ptb_sender import PTBSender
from senders.pytelegrambotapi_sender import PyTelegramBotAPISender
from reporting import json_reporter, md_reporter
from database_utils import setup_database, close_async_pool # Import DB utils

# Configuration
SENDER_CLASSES = {
    "httpx": HttpxSender,
    "aiohttp": AiohttpSender,
    "requests": RequestsSender,
    "urllib3": Urllib3Sender,
    "uplink": UplinkSender,
    "python-telegram-bot": PTBSender,
    "pytelegrambotapi": PyTelegramBotAPISender,
}

async def main():
    start_script_time = time.perf_counter()
    print(f"Starting {config.PROJECT_NAME}...")

    # --- Database Setup ---
    try:
        setup_database() # Initialize schema and populate if needed
    except Exception as e:
        print(f"Failed to setup database. Exiting. Error: {e}")
        sys.exit(1) # Exit if DB setup fails
    # ---------------------

    if config.TELEGRAM_BOT_TOKEN == 'YOUR_TELEGRAM_BOT_TOKEN' or \
       config.TELEGRAM_CHAT_ID == 'YOUR_TELEGRAM_CHAT_ID':
        print("ERROR: Please configure your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file or config.py before running.")
        return

    # Select senders to run
    senders_to_run_names = config.LIBRARIES_TO_TEST if config.LIBRARIES_TO_TEST else SENDER_CLASSES.keys()
    selected_senders = {name: SENDER_CLASSES[name] for name in senders_to_run_names if name in SENDER_CLASSES}

    if not selected_senders:
        print("No libraries selected or specified to test. Exiting.")
        print(f"Available libraries: {list(SENDER_CLASSES.keys())}")
        print(f"Configured to test: {config.LIBRARIES_TO_TEST}")
        return
    
    print(f"Selected libraries for benchmark: {list(selected_senders.keys())}")

    # Store results in a dictionary keyed by library name
    benchmark_results_by_library = {}

    for name, SenderClass in selected_senders.items(): # Iterate over items (name, class)
        print(f"\n--- Starting benchmark for {name} ---") # Use name for printing
        
        # Instantiate the sender
        sender_instance = SenderClass(
            config.TELEGRAM_BOT_TOKEN, 
            config.TELEGRAM_CHAT_ID, 
            config.TELEGRAM_API_URL_TEMPLATE,
            config  # Pass the config module itself
        )

        result_data = None
        if sender_instance.get_sender_type() == "async": # Use instance to call get_sender_type
            try:
                result_data = await sender_instance.run_benchmark_async(config.NUM_MESSAGES)
            except NotImplementedError:
                print(f"{name} async benchmark not implemented, skipping.")
            except Exception as e:
                print(f"Error during async benchmark for {name}: {e}")
        else:  # sync
            try:
                result_data = sender_instance.run_benchmark(config.NUM_MESSAGES)
            except NotImplementedError:
                print(f"{name} sync benchmark not implemented, skipping.")
            except Exception as e:
                print(f"Error during sync benchmark for {name}: {e}")
        
        if result_data:
            # Use the instance's library_name for storing, which should match 'name'
            benchmark_results_by_library[sender_instance.library_name.lower()] = result_data 
        
        print(f"--- Finished benchmark for {name} ---")

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
                "telegram_api_url": config.TELEGRAM_API_URL_TEMPLATE.format(token="[REDACTED]"),
                "database_backend": "PostgreSQL", # Added DB info
                "db_host": config.DB_HOST # Added DB info
            }
        },
        "libraries": benchmark_results_by_library, # Main results structured by library
        "overall_summary": {}
    }

    # Calculate overall summary based on the new structure
    if benchmark_results_by_library:
        # Filter for libraries that have workflow data and valid avg_total_processing_time_s
        valid_results_for_summary = [
            (name, lib_data["workflow"])
            for name, lib_data in benchmark_results_by_library.items()
            if "workflow" in lib_data and lib_data["workflow"].get("avg_total_processing_time_s") is not None and lib_data["workflow"]["avg_total_processing_time_s"] > 0
        ]

        if valid_results_for_summary:
            # Sort by avg_total_processing_time_s (includes DB + HTTP)
            fastest_total_time = min(valid_results_for_summary, key=lambda x: x[1]["avg_total_processing_time_s"])
            slowest_total_time = max(valid_results_for_summary, key=lambda x: x[1]["avg_total_processing_time_s"])
            
            # Sort by success_rate_percent
            most_reliable = max(valid_results_for_summary, key=lambda x: x[1]["success_rate_percent"])

            # Filter for resource rankings (where data might be present and non-zero)
            valid_for_memory = [(name, lib_data["workflow"]) for name, lib_data in benchmark_results_by_library.items() if "workflow" in lib_data and lib_data["workflow"].get("memory_increase_mb") is not None]
            valid_for_cpu = [(name, lib_data["workflow"]) for name, lib_data in benchmark_results_by_library.items() if "workflow" in lib_data and lib_data["workflow"].get("cpu_time_percent") is not None]

            lowest_mem_increase = min(valid_for_memory, key=lambda x: x[1]["memory_increase_mb"]) if valid_for_memory else (None, {"memory_increase_mb": 0})
            lowest_cpu_usage = min(valid_for_cpu, key=lambda x: x[1]["cpu_time_percent"]) if valid_for_cpu else (None, {"cpu_time_percent": 0})
            
            # Find best throughput (higher is better)
            highest_throughput = max(valid_results_for_summary, key=lambda x: x[1]["throughput_msg_per_sec"])

            # Find lowest standard deviation (lower is better - more consistent)
            lowest_std_dev_total = min(valid_results_for_summary, key=lambda x: x[1]["std_total_processing_time_s"])

            overall_summary_content = {
                "fastest_avg_total_processing_time_library": fastest_total_time[0],
                "fastest_avg_total_processing_time_s": fastest_total_time[1]["avg_total_processing_time_s"],
                "slowest_avg_total_processing_time_library": slowest_total_time[0],
                "slowest_avg_total_processing_time_s": slowest_total_time[1]["avg_total_processing_time_s"],
                
                "highest_throughput_library": highest_throughput[0],
                "highest_throughput_msg_per_sec": highest_throughput[1]["throughput_msg_per_sec"],
                
                "most_consistent_library_std_dev": lowest_std_dev_total[0], # Lower std dev is more consistent
                "lowest_std_dev_total_time_s": lowest_std_dev_total[1]["std_total_processing_time_s"],

                "highest_success_rate_library": most_reliable[0],
                "highest_success_rate_percent": most_reliable[1]["success_rate_percent"],
                "lowest_memory_library": lowest_mem_increase[0],
                "lowest_memory_increase_mb": lowest_mem_increase[1]["memory_increase_mb"],
                "lowest_cpu_library": lowest_cpu_usage[0],
                "lowest_cpu_time_percent": lowest_cpu_usage[1]["cpu_time_percent"],
                "rankings": { 
                    "avg_total_processing_time_s": sorted([ (lib_name, data["avg_total_processing_time_s"]) for lib_name, data in valid_results_for_summary], key=lambda x: x[1]),
                    "throughput_msg_per_sec": sorted([(lib_name, data["throughput_msg_per_sec"]) for lib_name, data in valid_results_for_summary], key=lambda x: x[1], reverse=True), # Higher is better
                    "std_total_processing_time_s": sorted([(lib_name, data["std_total_processing_time_s"]) for lib_name, data in valid_results_for_summary if data.get('std_total_processing_time_s') is not None], key=lambda x: x[1]), # Lower is better
                    "avg_db_read_time_s": sorted([ (lib_name, data["avg_db_read_time_s"]) for lib_name, data in valid_results_for_summary if data.get('avg_db_read_time_s') is not None], key=lambda x: x[1]),
                    "avg_http_send_time_s": sorted([ (lib_name, data["avg_http_send_time_s"]) for lib_name, data in valid_results_for_summary if data.get('avg_http_send_time_s') is not None], key=lambda x: x[1]),
                    "success_rate": sorted([ (lib_name, data["success_rate_percent"]) for lib_name, data in valid_results_for_summary], key=lambda x: x[1], reverse=True), # Keep this key for data, plot lookup uses different key
                    "avg_response_size_bytes": sorted([(lib_name, data["avg_response_size_bytes"]) for lib_name, data in valid_results_for_summary if data.get('avg_response_size_bytes') is not None], key=lambda x: x[1]), 
                    "memory_increase_mb": sorted([ (name, data["memory_increase_mb"]) for name, data in valid_for_memory], key=lambda x: x[1]) if valid_for_memory else [], # Standardized key
                    "cpu_time_percent": sorted([ (name, data["cpu_time_percent"]) for name, data in valid_for_cpu], key=lambda x: x[1]) if valid_for_cpu else [] # Standardized key
                }
            }
            benchmark_data_for_reports["overall_summary"] = overall_summary_content

    # Generate reports
    json_reporter.generate_report(benchmark_data_for_reports, config.REPORTS_DIR, config.JSON_REPORT_FILENAME)
    md_reporter.generate_report(benchmark_data_for_reports, config.REPORTS_DIR, config.MD_REPORT_FILENAME)
    
    end_script_time = time.perf_counter()
    print(f"\nBenchmark finished in {end_script_time - start_script_time:.2f} seconds.")
    print(f"Reports generated in '{config.REPORTS_DIR}' directory.")

    # --- Close async DB pool --- 
    await close_async_pool() # Close pool before main exits
    # --------------------------

if __name__ == "__main__":
    # Ensure async pool is closed properly - NO LONGER NEEDED HERE
    # try:
    #     asyncio.run(main())
    # finally:
    #     asyncio.run(close_async_pool()) # Close the pool on exit
    asyncio.run(main()) 