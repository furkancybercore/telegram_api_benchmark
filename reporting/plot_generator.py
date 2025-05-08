import os
import matplotlib
matplotlib.use('Agg') # Use a non-interactive backend for environments without a display
import matplotlib.pyplot as plt
import numpy as np

# Project specific imports - for accessing config like REPORTS_DIR if needed directly
# import config # Not strictly needed if output_dir is always passed

def generate_plots(report_data, output_dir):
    """Generate plots from report data and save them."""
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    libraries_data = report_data.get('libraries', {})
    if not libraries_data:
        print("No library data to plot.")
        return {}

    # Extract library names, ensuring they are strings for plotting
    library_names = [str(key) for key in libraries_data.keys()]
    plot_paths = {}

    # Metric 1: Average Telegram Send Time (s)
    avg_tg_send_times_s = []
    for lib_name in library_names:
        time_val = libraries_data.get(lib_name, {}).get('workflow', {}).get('avg_telegram_send_time_s', 0)
        avg_tg_send_times_s.append(float(time_val) if time_val is not None else 0)

    if any(t > 0 for t in avg_tg_send_times_s):
        plt.figure(figsize=(10, 6))
        plt.bar(library_names, avg_tg_send_times_s, color=['skyblue', 'lightcoral', 'lightgreen', 'gold', 'lightsalmon'])
        plt.ylabel('Time (seconds)')
        plt.title('Average Telegram Send Time per Library (Lower is Better)')
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        path = os.path.join(output_dir, 'plot_avg_telegram_send_time.png')
        plt.savefig(path)
        plot_paths['avg_telegram_send_time'] = os.path.basename(path)
        plt.close()
        print(f"Generated plot: {path}")
    else:
        print("Skipping plot_avg_telegram_send_time.png: No positive send times available.")

    # Metric 2: Successful vs Failed Runs (Stacked Bar Chart)
    successful_runs = []
    failed_runs = []
    total_runs_per_lib = []
    for lib_name in library_names:
        workflow_data = libraries_data.get(lib_name, {}).get('workflow', {})
        successful_runs.append(int(workflow_data.get('successful_runs', 0)))
        failed_runs.append(int(workflow_data.get('failed_runs', 0)))
        total_runs_per_lib.append(int(workflow_data.get('total_runs', 0)))
    
    # Use the num_messages from benchmark_details as the expected total if consistent
    # This provides a stable y-axis limit if some libraries failed entirely before all attempts
    num_messages_config = report_data.get("benchmark_details", {}).get("parameters", {}).get("num_messages_per_library", sum(total_runs_per_lib)/len(total_runs_per_lib) if total_runs_per_lib else 10)
    max_total_runs = int(num_messages_config) if num_messages_config > 0 else max(total_runs_per_lib) if total_runs_per_lib else 10

    if any(s > 0 or f > 0 for s, f in zip(successful_runs, failed_runs)):
        ind = np.arange(len(library_names))
        width = 0.35
        plt.figure(figsize=(12, 7))
        p1 = plt.bar(ind, successful_runs, width, color='lightgreen', label='Successful')
        p2 = plt.bar(ind, failed_runs, width, bottom=successful_runs, color='lightcoral', label='Failed')
        plt.ylabel('Number of Runs')
        plt.title(f'Workflow Run Success/Failure Rate (Total {max_total_runs} runs per library - Higher Successful is Better)')
        plt.xticks(ind, library_names, rotation=45, ha="right")
        plt.yticks(np.arange(0, max_total_runs + 1, max(1, max_total_runs // 10)))
        plt.legend()
        plt.tight_layout()
        path = os.path.join(output_dir, 'plot_success_failure_rate.png')
        plt.savefig(path)
        plot_paths['success_failure_rate'] = os.path.basename(path)
        plt.close()
        print(f"Generated plot: {path}")
    else:
        print("Skipping plot_success_failure_rate.png: No successful or failed runs to plot.")

    # Metric 3: Memory Increase (MB) - Placeholder data
    memory_increases_mb = []
    for lib_name in library_names:
        mem_val = libraries_data.get(lib_name, {}).get('workflow', {}).get('memory_increase_mb', 0)
        memory_increases_mb.append(float(mem_val) if mem_val is not None else 0)

    if any(m > 0 for m in memory_increases_mb): # Only plot if there's actual data > 0
        plt.figure(figsize=(10, 6))
        plt.bar(library_names, memory_increases_mb, color=['skyblue', 'lightcoral', 'lightgreen', 'gold', 'lightsalmon'])
        plt.ylabel('Memory Increase (MB)')
        plt.title('Memory Increase During Workflow per Library (Lower is Better)')
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        path = os.path.join(output_dir, 'plot_memory_increase.png')
        plt.savefig(path)
        plot_paths['memory_increase'] = os.path.basename(path)
        plt.close()
        print(f"Generated plot: {path}")
    else:
        print("Skipping plot_memory_increase.png: No memory increase data available.")

    # Metric 4: CPU Usage Percent - Placeholder data
    cpu_usages_percent = []
    for lib_name in library_names:
        cpu_val = libraries_data.get(lib_name, {}).get('workflow', {}).get('cpu_time_percent', 0)
        cpu_usages_percent.append(float(cpu_val) if cpu_val is not None else 0)
    
    if any(c > 0 for c in cpu_usages_percent): # Only plot if there's actual data > 0
        plt.figure(figsize=(10, 6))
        plt.bar(library_names, cpu_usages_percent, color=['skyblue', 'lightcoral', 'lightgreen', 'gold', 'lightsalmon'])
        plt.ylabel('CPU Usage (%)')
        plt.title('CPU Usage During Workflow per Library (Lower is Better)')
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        path = os.path.join(output_dir, 'plot_cpu_usage.png')
        plt.savefig(path)
        plot_paths['cpu_usage'] = os.path.basename(path)
        plt.close()
        print(f"Generated plot: {path}")
    else:
        print("Skipping plot_cpu_usage.png: No CPU usage data available.")

    return plot_paths 