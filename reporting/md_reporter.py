import os
import datetime

def generate_report(data, output_dir, filename):
    """Generates a Markdown report from the benchmark data."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    report_path = os.path.join(output_dir, filename)
    
    details = data.get("benchmark_details", {})
    results = data.get("results", [])
    overall_summary_data = data.get("overall_summary", {})

    md_content = []

    # Title
    md_content.append(f"# {details.get('project_name', 'Benchmark Report')}")
    md_content.append(f"_Generated on: {details.get('report_generated_at', datetime.datetime.now(datetime.timezone.utc).isoformat())}_")
    md_content.append("\n---\n")

    # Introduction / Methodology
    md_content.append("## 1. Introduction and Methodology")
    md_content.append("This report details the performance benchmarks of various Python HTTP libraries for sending messages to the Telegram API.")
    md_content.append(f"- **Number of Messages per Library:** {details.get('parameters', {}).get('num_messages', 'N/A')}")
    md_content.append(f"- **Telegram API URL:** `{details.get('parameters', {}).get('telegram_api_url', 'N/A')}`")
    md_content.append(f"- **Python Version:** {details.get('python_version', 'N/A')}")
    md_content.append(f"- **Platform:** {details.get('platform', 'N/A')}")
    md_content.append("\n### Libraries Tested:")
    lib_versions = details.get("libraries_versions", {})
    for lib, version in lib_versions.items():
        md_content.append(f"- `{lib}`: version `{version}`")
    if not lib_versions:
        md_content.append("- Versions not specified.")
    md_content.append("\n---\n")

    # Key Findings (Summary Table)
    md_content.append("## 2. Key Findings - Performance Summary")
    md_content.append("| Library         | Type    | Avg. Time (ms) | Min. Time (ms) | Max. Time (ms) | Success Rate (%) | Successful | Failed |")
    md_content.append("|-----------------|---------|----------------|----------------|----------------|------------------|------------|--------|")
    
    # Sort results by average time for the table
    sorted_results = sorted(results, key=lambda x: x.get('summary', {}).get('average_time_ms', float('inf')) if x.get('summary', {}).get('average_time_ms') is not None else float('inf'))
    
    for res in sorted_results:
        summary = res.get("summary", {})
        avg_time = summary.get('average_time_ms', '-')
        min_time = summary.get('min_time_ms', '-')
        max_time = summary.get('max_time_ms', '-')
        success_rate = summary.get('success_rate_percent', '-')
        
        avg_time_str = f"{avg_time:.2f}" if isinstance(avg_time, (int, float)) else str(avg_time)
        min_time_str = f"{min_time:.2f}" if isinstance(min_time, (int, float)) else str(min_time)
        max_time_str = f"{max_time:.2f}" if isinstance(max_time, (int, float)) else str(max_time)
        success_rate_str = f"{success_rate:.2f}" if isinstance(success_rate, (int, float)) else str(success_rate)
        
        md_content.append(f"| {res.get('library', 'N/A')} | {res.get('type', 'N/A')} | {avg_time_str} | {min_time_str} | {max_time_str} | {success_rate_str} | {summary.get('successful_requests', '-')} | {summary.get('failed_requests', '-')} |")
    md_content.append("\n---\n")

    # Detailed Results per Library
    md_content.append("## 3. Detailed Results per Library")
    for i, res in enumerate(results):
        md_content.append(f"\n### 3.{i + 1}. {res.get('library', 'N/A')} ({res.get('type', 'N/A')})")
        summary = res.get("summary", {})
        total_sent = summary.get('successful_requests', 0) + summary.get('failed_requests', 0)
        
        avg_time = summary.get('average_time_ms', '-')
        min_time = summary.get('min_time_ms', '-')
        max_time = summary.get('max_time_ms', '-')
        success_rate = summary.get('success_rate_percent', '-')
        total_time = summary.get('total_time_ms', '-')

        avg_time_str = f"{avg_time:.2f} ms" if isinstance(avg_time, (int, float)) else str(avg_time)
        min_time_str = f"{min_time:.2f} ms" if isinstance(min_time, (int, float)) else str(min_time)
        max_time_str = f"{max_time:.2f} ms" if isinstance(max_time, (int, float)) else str(max_time)
        success_rate_str = f"{success_rate:.2f}%" if isinstance(success_rate, (int, float)) else str(success_rate)
        total_time_str = f"{total_time:.2f} ms" if isinstance(total_time, (int, float)) else str(total_time)

        md_content.append(f"- **Total Messages Attempted:** {total_sent}")
        md_content.append(f"- **Successful:** {summary.get('successful_requests', '-')}")
        md_content.append(f"- **Failed:** {summary.get('failed_requests', '-')}")
        md_content.append(f"- **Success Rate:** {success_rate_str}")
        md_content.append(f"- **Total Time for All Requests:** {total_time_str}")
        md_content.append(f"- **Average Request Time (for successful):** {avg_time_str}")
        md_content.append(f"- **Min Request Time (for successful):** {min_time_str}")
        md_content.append(f"- **Max Request Time (for successful):** {max_time_str}")

    md_content.append("\n---\n")

    # Overall Summary from JSON
    md_content.append("## 4. Overall Comparison Summary")
    if overall_summary_data.get("fastest_library_avg_time"):
        avg_time = overall_summary_data.get('fastest_avg_time_ms', 'N/A')
        avg_time_str = f"({avg_time:.2f} ms)" if isinstance(avg_time, (int, float)) else ""
        md_content.append(f"- **Fastest (Avg. Time):** {overall_summary_data.get('fastest_library_avg_time')} {avg_time_str}")
    if overall_summary_data.get("slowest_library_avg_time"):
        avg_time = overall_summary_data.get('slowest_avg_time_ms', 'N/A')
        avg_time_str = f"({avg_time:.2f} ms)" if isinstance(avg_time, (int, float)) else ""
        md_content.append(f"- **Slowest (Avg. Time):** {overall_summary_data.get('slowest_library_avg_time')} {avg_time_str}")
    if overall_summary_data.get("most_reliable_library"):
        success_rate = overall_summary_data.get('highest_success_rate', 'N/A')
        success_rate_str = f"({success_rate:.2f}%)" if isinstance(success_rate, (int, float)) else ""
        md_content.append(f"- **Most Reliable (Success Rate):** {overall_summary_data.get('most_reliable_library')} {success_rate_str}")
    md_content.append("\n_Note: CPU and Memory usage comparisons are placeholders in this version and would require further specific tooling to measure accurately per library._")
    md_content.append("\n---\n")
    
    # Placeholder for Plots
    md_content.append("## 5. Visualizations (Data for Plots)")
    md_content.append("The raw data for generating plots (like average send times, success/failure rates) is available in the JSON report.")
    md_content.append("Example plots that can be generated:")
    md_content.append("- `plot_avg_telegram_send_time.png`: Bar chart of average send times per library.")
    md_content.append("- `plot_success_failure_rate.png`: Stacked bar chart of success vs. failure counts or rates.")
    md_content.append("_(Generating these plots directly is outside the scope of this script but the data is provided in the JSON output)._")

    try:
        with open(report_path, 'w') as f:
            f.write("\n".join(md_content))
        print(f"Markdown report generated: {report_path}")
    except IOError as e:
        print(f"Error writing Markdown report to {report_path}: {e}") 