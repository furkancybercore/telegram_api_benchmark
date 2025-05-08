import os
import datetime
from .plot_generator import generate_plots # Import the new plot generator
import config # To get REPORTS_DIR for plot paths if needed, or pass output_dir

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

    md_content = []

    # --- Report Header ---
    md_content.append(f"# {details.get('project_name', 'HTTP Client Libraries Workflow Benchmark Report')}")
    md_content.append("## Overview")
    md_content.append(f"- **Date:** {datetime.datetime.fromisoformat(details.get('timestamp', datetime.datetime.now(datetime.timezone.utc).isoformat())).strftime('%Y-%m-%d %H:%M:%S')}")
    md_content.append(f"- **Number of Messages per Library:** {details.get('parameters', {}).get('num_messages_per_library', 'N/A')}")
    lib_names_str = ", ".join(libraries.keys())
    md_content.append(f"- **Libraries Tested:** {lib_names_str if lib_names_str else 'None'}")
    md_content.append(f"- **Python Version:** {details.get('python_version', 'N/A')}")
    md_content.append(f"- **Platform:** {details.get('platform', 'N/A')}")
    md_content.append("\n---\n")

    # --- Summary of Best Performers ---
    md_content.append("## Summary of Best Performers")
    md_content.append(f"- **Fastest Avg. Total Processing Time (DB+HTTP):** {summary_overall.get('fastest_avg_total_processing_time_library', 'N/A')} ({summary_overall.get('fastest_avg_total_processing_time_s', 0):.4f}s)")
    md_content.append(f"- **Highest Throughput:** {summary_overall.get('highest_throughput_library', 'N/A')} ({summary_overall.get('highest_throughput_msg_per_sec', 0):.2f} msg/s)")
    md_content.append(f"- **Most Consistent (Lowest Std Dev - Total Time):** {summary_overall.get('most_consistent_library_std_dev', 'N/A')} ({summary_overall.get('lowest_std_dev_total_time_s', 0):.4f}s)")
    md_content.append(f"- **Highest Success Rate:** {summary_overall.get('highest_success_rate_library', 'N/A')} ({summary_overall.get('highest_success_rate_percent', 0):.2f}%)")
    md_content.append(f"- **Lowest Memory Usage:** {summary_overall.get('lowest_memory_library', 'N/A')} ({summary_overall.get('lowest_memory_increase_mb', 0):.2f} MB)")
    md_content.append(f"- **Lowest CPU Usage:** {summary_overall.get('lowest_cpu_library', 'N/A')} ({summary_overall.get('lowest_cpu_time_percent', 0):.2f}%)")
    md_content.append("\n---\n")

    # --- Performance Rankings & Visualizations ---
    md_content.append("## Performance Rankings & Visualizations")
    rankings = summary_overall.get("rankings", {})

    # Helper function now only adds title, description, and plot
    def add_ranking_section(metric_key, title, description):
        plot_filename = plot_filenames.get(metric_key)
        # Only add section if plot exists
        if plot_filename:
            md_content.append(f"\n### {title}")
            md_content.append(f"> _{description}_\n") # Add description
            md_content.append(f"\n![{title} Plot]({plot_filename})\n")
        else:
            # Optionally mention if plot is missing for a key metric
            print(f"Note: Plot not generated for metric '{metric_key}', skipping section.")
            pass # Don't add the section if no plot

    # Call helper with descriptions and simplified titles
    add_ranking_section("avg_total_processing_time_s", "Total Processing Time (DB+HTTP)", 
                      "Average time per message (DB read + Telegram send). Lower is better.")
    add_ranking_section("throughput_msg_per_sec", "Throughput", 
                      "Messages processed per second. Higher indicates better efficiency.")
    add_ranking_section("std_total_processing_time_s", "Total Processing Time Consistency (Std Dev)",
                      "Standard deviation of total processing time. Lower indicates more predictable performance.")
    add_ranking_section("avg_http_send_time_s", "HTTP Send Time",
                      "Average time for the Telegram API request only. Lower is better.")
    add_ranking_section("std_http_send_time_s", "HTTP Send Time Consistency (Std Dev)",
                      "Standard deviation of HTTP send time. Lower indicates less network variation.")
    add_ranking_section("avg_db_read_time_s", "DB Read Time",
                      "Average time to read from PostgreSQL. Lower is better.")
    # Use the plot key for success rate here
    add_ranking_section("success_rate", "Success Rate", 
                      "Percentage of attempts (DB read + Telegram send) that completed successfully. Higher is better.")
    add_ranking_section("avg_response_size_bytes", "Telegram API Response Size",
                      "Average size of the response from Telegram API. Smaller indicates less overhead.")

    md_content.append("\n## Resource Usage (Lower is Better)")
    add_ranking_section("memory_increase_mb", "Memory Usage",
                      "Increase in Python process RAM from start to end of the benchmark. Lower is better.")
    add_ranking_section("cpu_time_percent", "CPU Usage",
                      "Average CPU percentage used by the Python process during the benchmark. Lower is better.")
    
    md_content.append("\n---\n")
    md_content.append("## Conclusion")
    md_content.append("This benchmark measures the performance of different Python HTTP client libraries for sending messages to the Telegram API. "
                      "The metrics focus on database read time, Telegram message send time, total processing time, throughput, success rates, latency consistency (standard deviation), and resource utilization.")

    try:
        with open(report_path, 'w') as f:
            f.write("\n".join(md_content))
        print(f"Markdown report generated: {report_path}")
    except IOError as e:
        print(f"Error writing Markdown report to {report_path}: {e}") 