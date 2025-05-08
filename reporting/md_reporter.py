import os
import datetime
from .plot_generator import generate_plots # Import the new plot generator
import config # To get REPORTS_DIR for plot paths if needed, or pass output_dir
from datetime import timezone, timedelta

def generate_report(report_data, output_dir, filename):
    """Generates a Markdown report from the benchmark data, including plots."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    report_path = os.path.join(output_dir, filename)

    # Step 1: Generate plots using the new plot_generator
    # generate_plots expects the full report_data to extract library details and benchmark_details
    # It will save plots into the same output_dir
    # The paths returned by generate_plots are relative to output_dir (basenames)
    plot_filenames = generate_plots(report_data, output_dir)

    # Extract necessary data for MD generation
    details = report_data.get("benchmark_details", {})
    libraries = report_data.get("libraries", {})
    summary_overall = report_data.get("overall_summary", {})
    rankings = summary_overall.get("rankings", {})

    md_content = []

    # --- Report Header ---
    md_content.append(f"# {details.get('project_name', 'HTTP Client Libraries Workflow Benchmark Report')}")
    md_content.append("## Overview")
    
    # Convert timestamp to Sydney time (+10)
    timestamp_str = details.get('timestamp', datetime.datetime.now(timezone.utc).isoformat())
    try:
        timestamp = datetime.datetime.fromisoformat(timestamp_str)
        # Convert to Sydney time (+10)
        sydney_tz = timezone(timedelta(hours=10))
        sydney_time = timestamp.astimezone(sydney_tz)
        formatted_time = sydney_time.strftime('%Y-%m-%d %H:%M:%S (Sydney UTC+10)')
    except:
        formatted_time = timestamp_str
        
    md_content.append(f"- **Date:** {formatted_time}")
    md_content.append(f"- **Number of Messages per Library:** {details.get('parameters', {}).get('num_messages_per_library', 'N/A')}")
    lib_names_str = ", ".join(libraries.keys())
    md_content.append(f"- **Libraries Tested:** {lib_names_str if lib_names_str else 'None'}")
    md_content.append(f"- **Python Version:** {details.get('python_version', 'N/A')}")
    md_content.append(f"- **Platform:** {details.get('platform', 'N/A')}")
    md_content.append(f"- **GitHub Project:** [telegram_api_benchmark](https://github.com/furkancybercore/telegram_api_benchmark)")
    md_content.append("\n---\n")

    # --- Add Test Methodology Section ---
    md_content.append("## Test Methodology")
    md_content.append("This benchmark test was conducted using the following steps:")
    md_content.append("- We created a PostgreSQL database to store test messages")
    md_content.append("- For each HTTP library, we:")
    md_content.append("  - Read messages from the database")
    md_content.append("  - Sent these messages to the Telegram API")
    md_content.append("  - Measured performance and resource usage")
    md_content.append("- Due to Telegram's message limit (20 messages per minute), we sent messages to a personal Telegram account instead of a channel")
    md_content.append("- This allowed us to run 1000 tests for each method")
    md_content.append("- We compared different Python HTTP libraries including requests, httpx, aiohttp, urllib3, etc.")
    md_content.append("- Each test measures success rate, speed, and computer resource usage")
    md_content.append("\n---\n")

    # --- Summary of Best Performers with bullets instead of nested headings ---
    md_content.append("## Summary of Best Performers")
    
    # Performance metrics summary - no level 3 heading, just bold text
    md_content.append("**Performance Metrics:**")
    
    # Success Rate
    success_rate_lib = summary_overall.get('highest_success_rate_library', 'N/A')
    success_rate_val = summary_overall.get('highest_success_rate_percent', 0)
    # Get all libraries with the same success rate
    success_rate_libs = []
    for lib, rate in rankings.get("success_rate", []):
        if rate == success_rate_val:
            success_rate_libs.append(lib)
    success_rate_libs_str = ", ".join(success_rate_libs) if success_rate_libs else success_rate_lib
    # Replace any occurrence of "ptb" with "python-telegram-bot"
    success_rate_libs_str = success_rate_libs_str.replace("ptb", "python-telegram-bot")
    md_content.append(f"- **Success Rate:** {success_rate_val:.2f}% ({success_rate_libs_str})")
    
    # Total Processing Time
    fastest_lib = summary_overall.get('fastest_avg_total_processing_time_library', 'N/A')
    fastest_lib = fastest_lib.replace("ptb", "python-telegram-bot")
    md_content.append(f"- **Total Processing Time:** {summary_overall.get('fastest_avg_total_processing_time_s', 0):.4f}s ({fastest_lib})")
    
    # Throughput
    highest_throughput_lib = summary_overall.get('highest_throughput_library', 'N/A')
    highest_throughput_lib = highest_throughput_lib.replace("ptb", "python-telegram-bot")
    md_content.append(f"- **Throughput:** {summary_overall.get('highest_throughput_msg_per_sec', 0):.2f} msg/s ({highest_throughput_lib})")
    
    # HTTP Send Time
    fastest_http_lib = summary_overall.get('fastest_avg_http_send_time_library', 'N/A')
    fastest_http_lib = fastest_http_lib.replace("ptb", "python-telegram-bot")
    md_content.append(f"- **HTTP Send Time:** {summary_overall.get('fastest_avg_http_send_time_s', 0):.4f}s ({fastest_http_lib})")
    
    # DB Read Time
    fastest_db_lib = summary_overall.get('fastest_avg_db_read_time_library', 'N/A')
    fastest_db_lib = fastest_db_lib.replace("ptb", "python-telegram-bot")
    md_content.append(f"- **DB Read Time:** {summary_overall.get('fastest_avg_db_read_time_s', 0):.5f}s ({fastest_db_lib})")
    
    # Consistency (Std Dev)
    most_consistent_lib = summary_overall.get('most_consistent_library_std_dev', 'N/A')
    most_consistent_lib = most_consistent_lib.replace("ptb", "python-telegram-bot")
    md_content.append(f"- **Consistency (Lowest Std Dev):** {summary_overall.get('lowest_std_dev_total_time_s', 0):.4f}s ({most_consistent_lib})")
    
    # Response Size
    smallest_response_lib = summary_overall.get('smallest_avg_response_size_library', 'N/A')
    smallest_response_lib = smallest_response_lib.replace("ptb", "python-telegram-bot")
    md_content.append(f"- **Response Size:** {summary_overall.get('smallest_avg_response_size_bytes', 0):.1f} bytes ({smallest_response_lib})")

    # Resource Usage metrics summary - no level 3 heading, just bold text
    md_content.append(" ")
    md_content.append("**Resource Usage Metrics:**")
    
    # CPU Usage
    cpu_lib = summary_overall.get('lowest_cpu_library', 'N/A')
    cpu_val = summary_overall.get('lowest_cpu_time_percent', 0)
    # Get all libraries with 0.00% CPU usage
    cpu_libs = []
    for lib, usage in rankings.get("cpu_time_percent", []):
        if usage == cpu_val:
            cpu_libs.append(lib)
    cpu_libs_str = ", ".join(cpu_libs) if cpu_libs else cpu_lib
    cpu_libs_str = cpu_libs_str.replace("ptb", "python-telegram-bot")
    md_content.append(f"- **CPU Usage:** {cpu_val:.2f}% ({cpu_libs_str})")
    
    # Memory Usage
    lowest_memory_lib = summary_overall.get('lowest_memory_library', 'N/A')
    lowest_memory_lib = lowest_memory_lib.replace("ptb", "python-telegram-bot")
    md_content.append(f"- **Memory Usage:** {summary_overall.get('lowest_memory_increase_mb', 0):.2f} MB ({lowest_memory_lib})")
    
    md_content.append("\n---\n")

    # --- Complete Metrics Table ---
    md_content.append("## All Metrics Comparison")
    md_content.append("The table below compares all libraries across the key metrics:")
    
    # Define table headers with metrics in desired order
    table_headers = [
        "Library", 
        "Success Rate (%)", 
        "Throughput (msg/s)",
        "Avg Total Time (s)", 
        "Std Dev Total (s)",
        "CPU Usage (%)",
        "Memory (MB)",
        "Avg HTTP Time (s)",
        "Avg DB Read (s)",
        "Avg Response Size (B)"
    ]
    
    # Start table
    md_content.append("\n| " + " | ".join(table_headers) + " |")
    md_content.append("| " + " | ".join(["---" for _ in table_headers]) + " |")
    
    # Add a row for each library
    for lib_name, lib_data in libraries.items():
        # Replace ptb with full name
        display_lib_name = lib_name.replace("ptb", "python-telegram-bot") 
        workflow = lib_data.get("workflow", {})
        row = [
            display_lib_name,
            f"{workflow.get('success_rate_percent', 0):.2f}",
            f"{workflow.get('throughput_msg_per_sec', 0):.2f}",
            f"{workflow.get('avg_total_processing_time_s', 0):.4f}",
            f"{workflow.get('std_total_processing_time_s', 0):.4f}",
            f"{workflow.get('cpu_time_percent', 0):.2f}",
            f"{workflow.get('memory_increase_mb', 0):.2f}",
            f"{workflow.get('avg_http_send_time_s', 0):.4f}",
            f"{workflow.get('avg_db_read_time_s', 0):.5f}",
            f"{workflow.get('avg_response_size_bytes', 0):.1f}"
        ]
        md_content.append("| " + " | ".join(row) + " |")
    
    md_content.append("\n---\n")

    # --- Visualizations: Reordered with Performance and Resource Usage as main sections ---
    
    # Helper function to add section with plot
    def add_plot_section(metric_key, title, description):
        plot_filename = plot_filenames.get(metric_key)
        if plot_filename:
            md_content.append(f"\n#### {title}")
            md_content.append(f"> _{description}_\n")
            md_content.append(f"\n![{title} Plot]({plot_filename})\n")
        else:
            print(f"Note: Plot not generated for metric '{metric_key}', skipping section.")
    
    # Performance section with reordered metrics (success rate first)
    md_content.append("## Performance")
    
    # Success Rate (most important)
    add_plot_section("success_rate", "Success Rate", 
                     "Number of attempts (DB read + Telegram send) that completed successfully. Higher is better.")
    
    # Throughput
    add_plot_section("throughput_msg_per_sec", "Throughput", 
                     "Messages processed per second. Higher indicates better efficiency.")
    
    # Total Processing Time and Consistency
    add_plot_section("avg_total_processing_time_s", "Total Processing Time", 
                     "Average time per message (DB read + Telegram send). Lower is better.")
    add_plot_section("std_total_processing_time_s", "Processing Time Consistency", 
                     "Standard deviation of total processing time. Lower indicates more predictable performance.")
    
    # HTTP metrics
    add_plot_section("avg_http_send_time_s", "HTTP Send Time",
                     "Average time for the Telegram API request only. Lower is better.")
    add_plot_section("std_http_send_time_s", "HTTP Time Consistency",
                     "Standard deviation of HTTP send time. Lower indicates less network variation.")
    
    # DB Read Time
    add_plot_section("avg_db_read_time_s", "DB Read Time",
                     "Average time to read from PostgreSQL. Lower is better.")
    
    # Response Size
    add_plot_section("avg_response_size_bytes", "Response Size",
                     "Average size of the response from Telegram API. Smaller indicates less overhead.")
    
    # Resource Usage section with CPU first
    md_content.append("## Resource Usage")
    
    # CPU Usage (more important)
    add_plot_section("cpu_time_percent", "CPU Usage",
                     "Average CPU percentage used by the Python process during the benchmark. Lower is better.")
    
    # Memory Usage
    add_plot_section("memory_increase_mb", "Memory Usage",
                     "Increase in Python process RAM from start to end of the benchmark. Lower is better.")
    
    md_content.append("\n---\n")
    
    # Updated conclusion with bullets and B2 English level

    """
    This benchmark measures the performance of different Python HTTP client libraries for sending messages to the Telegram API. 
    The metrics focus on success rates, throughput, processing times, consistency, and resource utilization to help you choose the most suitable library for your use case.
    """
    md_content.append("## Conclusion")
    md_content.append("- This benchmark shows how different Python libraries work when sending messages to Telegram")
    md_content.append("- The metrics focus on;")
    md_content.append(" -- resource utilization")
    md_content.append(" -- success rates")
    md_content.append(" -- throughput")
    md_content.append(" -- processing times")
    md_content.append(" -- consistency")
    md_content.append("- We should choose the library that matches our project's specific needs")

    try:
        with open(report_path, 'w') as f:
            f.write("\n".join(md_content))
        print(f"Markdown report generated: {report_path}")
    except IOError as e:
        print(f"Error writing Markdown report to {report_path}: {e}") 