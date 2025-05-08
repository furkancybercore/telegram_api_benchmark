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
    md_content.append(f"- **Fastest Avg. Telegram Send Time:** {summary_overall.get('fastest_avg_telegram_send_time', 'N/A')} ({summary_overall.get('fastest_avg_telegram_send_time_s', 0):.4f}s)")
    # Add other "best performers" if available in summary_overall, e.g., workflow time
    md_content.append(f"- **Highest Success Rate:** {summary_overall.get('highest_success_rate_library', 'N/A')} ({summary_overall.get('highest_success_rate_percent', 0):.2f}%)")
    md_content.append(f"- **Lowest Memory Usage (Workflow):** {summary_overall.get('lowest_memory_library', 'N/A')} ({summary_overall.get('lowest_memory_increase_mb', 0):.2f} MB)")
    md_content.append(f"- **Lowest CPU Usage (Workflow):** {summary_overall.get('lowest_cpu_library', 'N/A')} ({summary_overall.get('lowest_cpu_time_percent', 0):.2f}%)")
    md_content.append("\n---\n")

    # --- Detailed Results per Library ---
    md_content.append("## Detailed Results per Library")
    md_content.append("| Library | Version | Avg TG Send (s) | Min TG Send (s) | Max TG Send (s) | Total Runs | Success Runs | Failed Runs | Success Rate (%) | CPU (%) | Memory (MB) |")
    md_content.append("|---------|---------|-----------------|-----------------|-----------------|------------|--------------|-------------|------------------|---------|-------------|")
    for lib_name, lib_data in libraries.items():
        workflow_metrics = lib_data.get("workflow", {})
        version = lib_data.get("version", "N/A")
        md_content.append(
            f"| {lib_name} | {version} | "
            f"{workflow_metrics.get('avg_telegram_send_time_s', 0):.4f} | "
            f"{workflow_metrics.get('min_telegram_send_time_s', 0):.4f} | "
            f"{workflow_metrics.get('max_telegram_send_time_s', 0):.4f} | "
            f"{workflow_metrics.get('total_runs', 0)} | "
            f"{workflow_metrics.get('successful_runs', 0)} | "
            f"{workflow_metrics.get('failed_runs', 0)} | "
            f"{workflow_metrics.get('success_rate_percent', 0):.2f} | "
            f"{workflow_metrics.get('cpu_time_percent', 0):.2f} | "
            f"{workflow_metrics.get('memory_increase_mb', 0):.2f} |"
        )
    md_content.append("\n---\n")

    # --- Performance Rankings and Plots ---
    md_content.append("## Performance Rankings & Visualizations")
    rankings = summary_overall.get("rankings", {})

    if rankings.get("avg_telegram_send_time"):
        md_content.append("\n### Fastest Average Telegram Send Time")
        if plot_filenames.get('avg_telegram_send_time'):
             md_content.append(f"\n![Avg TG Send Time Plot]({plot_filenames['avg_telegram_send_time']})\n")
        md_content.append("| Rank | Library | Avg Time (s) |")
        md_content.append("|------|---------|--------------|")
        for i, (lib, time_val) in enumerate(rankings["avg_telegram_send_time"]):
            md_content.append(f"| {i+1} | {lib} | {time_val:.4f} |")
        md_content.append("")
            
    if rankings.get("success_rate"):
        md_content.append("\n### Highest Success Rate")
        if plot_filenames.get('success_failure_rate'):
             md_content.append(f"\n![Success/Failure Rate Plot]({plot_filenames['success_failure_rate']})\n")
        md_content.append("| Rank | Library | Success Rate (%) |")
        md_content.append("|------|---------|------------------|")
        for i, (lib, rate) in enumerate(rankings["success_rate"]):
            md_content.append(f"| {i+1} | {lib} | {rate:.2f} |")
        md_content.append("")

    # --- Resource Usage Rankings (Placeholders for now) ---
    md_content.append("\n## Resource Usage Rankings (Lower is Better - Placeholders)")
    if rankings.get("memory_usage") or plot_filenames.get('memory_increase'): # Show section if plot exists or data structure exists
        md_content.append("\n### Lowest Memory Usage (Workflow)")
        if plot_filenames.get('memory_increase'):
             md_content.append(f"\n![Memory Usage Plot]({plot_filenames['memory_increase']})\n")
        if rankings.get("memory_usage"):
            md_content.append("| Rank | Library | Memory Increase (MB) |")
            md_content.append("|------|---------|----------------------|")
            for i, (lib, mem) in enumerate(rankings["memory_usage"]):
                md_content.append(f"| {i+1} | {lib} | {mem:.2f} |")
        md_content.append("")

    if rankings.get("cpu_usage") or plot_filenames.get('cpu_usage'):
        md_content.append("\n### Lowest CPU Usage (Workflow)")
        if plot_filenames.get('cpu_usage'):
             md_content.append(f"\n![CPU Usage Plot]({plot_filenames['cpu_usage']})\n")
        if rankings.get("cpu_usage"):
            md_content.append("| Rank | Library | CPU Usage (%) |")
            md_content.append("|------|---------|---------------|")
            for i, (lib, cpu) in enumerate(rankings["cpu_usage"]):
                md_content.append(f"| {i+1} | {lib} | {cpu:.2f} |")
        md_content.append("")
    
    md_content.append("\n---\n")
    md_content.append("## Conclusion")
    md_content.append("This benchmark measures the performance of different Python HTTP client libraries for sending messages to the Telegram API. "
                      "The metrics focus on the Telegram message send time, success rates, and resource utilization.")

    try:
        with open(report_path, 'w') as f:
            f.write("\n".join(md_content))
        print(f"Markdown report generated: {report_path}")
    except IOError as e:
        print(f"Error writing Markdown report to {report_path}: {e}") 