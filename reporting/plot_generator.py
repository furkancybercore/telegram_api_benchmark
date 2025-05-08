import os
import matplotlib
matplotlib.use('Agg') # Use a non-interactive backend for environments without a display
import matplotlib.pyplot as plt
import numpy as np

# Project specific imports - for accessing config like REPORTS_DIR if needed directly
# import config # Not strictly needed if output_dir is always passed

# Helper function to add labels to bars
def add_labels(ax, unit="", format_spec=".2f"):
    try:
        decimals = int(format_spec.split('.')[-1][0])
    except:
        decimals = 2 # Default
    fmt = f'%.{decimals}f{unit}' # Construct format string like '%.4fs' or '%.2f%'
    
    for container in ax.containers:
        ax.bar_label(container, fmt=fmt, label_type='edge', fontsize=8, padding=3)

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
    base_colors = ['skyblue', 'lightcoral', 'lightgreen', 'gold', 'lightsalmon', 'plum']
    colors = base_colors[:len(library_names)] if len(library_names) <= len(base_colors) else base_colors # Adjust colors

    # --- Time-based Plots (Seconds) ---
    time_metrics_to_plot = [
        ("avg_total_processing_time_s", "Avg Total Processing Time (DB+HTTP)", "plot_avg_total_processing_time.png", ".4f"),
        ("avg_http_send_time_s", "Avg HTTP Send Time", "plot_avg_http_send_time.png", ".4f"),
        ("avg_db_read_time_s", "Avg DB Read Time", "plot_avg_db_read_time.png", ".5f"),
        ("p95_total_processing_time_s", "P95 Total Processing Time", "plot_p95_total_time.png", ".4f"),
        ("p95_http_send_time_s", "P95 HTTP Send Time", "plot_p95_http_time.png", ".4f"),
        ("std_total_processing_time_s", "Std Dev Total Processing Time", "plot_std_total_time.png", ".4f"), 
        ("std_http_send_time_s", "Std Dev HTTP Send Time", "plot_std_http_time.png", ".4f"), 
    ]

    for metric_key, base_title, filename, fmt_spec in time_metrics_to_plot:
        values = [float(libraries_data.get(lib_name, {}).get('workflow', {}).get(metric_key, 0) or 0) for lib_name in library_names]
        
        if any(v != 0 for v in values): # Plot if any non-zero data
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(library_names, values, color=colors)
            ax.set_ylabel('Time (seconds)') 
            ax.set_title(f"{base_title} (Lower is Better)") 
            ax.tick_params(axis='x', rotation=45)
            add_labels(ax, unit="s", format_spec=fmt_spec) 
            fig.tight_layout()
            path = os.path.join(output_dir, filename)
            plt.savefig(path)
            plot_paths[metric_key] = os.path.basename(path)
            plt.close(fig)
            print(f"Generated plot: {path}")
        else:
            print(f"Skipping {filename}: No non-zero data for {metric_key}.")

    # --- Throughput Plot ---
    throughput_values = [float(libraries_data.get(lib_name, {}).get('workflow', {}).get('throughput_msg_per_sec', 0) or 0) for lib_name in library_names]
    if any(v > 0 for v in throughput_values):
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(library_names, throughput_values, color=colors)
        ax.set_ylabel('Messages per Second')
        ax.set_title('Throughput (Higher is Better)')
        ax.tick_params(axis='x', rotation=45)
        add_labels(ax, unit=" msg/s", format_spec=".2f")
        fig.tight_layout()
        path = os.path.join(output_dir, 'plot_throughput.png')
        plt.savefig(path)
        plot_paths['throughput_msg_per_sec'] = os.path.basename(path)
        plt.close(fig)
        print(f"Generated plot: {path}")
    else:
        print(f"Skipping plot_throughput.png: No positive data.")

    # --- Success Rate Plot ---
    successful_runs = [int(libraries_data.get(lib_name, {}).get('workflow', {}).get('successful_runs', 0)) for lib_name in library_names]
    failed_runs = [int(libraries_data.get(lib_name, {}).get('workflow', {}).get('failed_runs', 0)) for lib_name in library_names]
    total_runs_per_lib = [int(libraries_data.get(lib_name, {}).get('workflow', {}).get('total_runs', 0)) for lib_name in library_names]
    num_messages_config = report_data.get("benchmark_details", {}).get("parameters", {}).get("num_messages_per_library", sum(total_runs_per_lib)/len(total_runs_per_lib) if total_runs_per_lib else 10)
    max_total_runs = int(num_messages_config) if num_messages_config > 0 else max(total_runs_per_lib) if total_runs_per_lib else 10

    if True: # Always generate this plot even if all fail
        ind = np.arange(len(library_names))
        width = 0.35
        fig, ax = plt.subplots(figsize=(12, 7))
        p1 = ax.bar(ind, successful_runs, width, color='lightgreen', label='Successful')
        p2 = ax.bar(ind, failed_runs, width, bottom=successful_runs, color='lightcoral', label='Failed')
        ax.set_ylabel('Number of Runs')
        ax.set_title(f'Success/Failure Rate (Total {max_total_runs} runs) (Higher Successful is Better)')
        ax.set_xticks(ind)
        ax.set_xticklabels(library_names, rotation=45, ha="right")
        ax.set_yticks(np.arange(0, max_total_runs + 1, max(1, max_total_runs // 10)))
        ax.legend()
        if any(s > 0 for s in successful_runs): ax.bar_label(p1, fmt='%g', label_type='center', fontsize=8)
        if any(f > 0 for f in failed_runs): ax.bar_label(p2, fmt='%g', label_type='center', fontsize=8)
        fig.tight_layout()
        path = os.path.join(output_dir, 'plot_success_failure_rate.png')
        plt.savefig(path)
        plot_paths['success_rate'] = os.path.basename(path) 
        plt.close(fig)
        print(f"Generated plot: {path}")

    # --- Resource Usage Plots ---
    resource_metrics_to_plot = [
        ("memory_increase_mb", "Memory Usage", "Memory Increase (MB)", "plot_memory_increase.png", ".2f", " MB"),
        ("cpu_time_percent", "CPU Usage", "CPU Usage (%)", "plot_cpu_usage.png", ".2f", "%"),
    ]

    for metric_key, base_title, ylabel, filename, fmt_spec, unit in resource_metrics_to_plot:
        values = [float(libraries_data.get(lib_name, {}).get('workflow', {}).get(metric_key, 0) or 0) for lib_name in library_names]
        if True: # Always plot resource usage for comparison
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(library_names, values, color=colors)
            ax.set_ylabel(ylabel)
            ax.set_title(f"{base_title} (Lower is Better)")
            ax.tick_params(axis='x', rotation=45)
            add_labels(ax, unit=unit, format_spec=fmt_spec) 
            fig.tight_layout()
            path = os.path.join(output_dir, filename)
            plt.savefig(path)
            plot_paths[metric_key] = os.path.basename(path)
            plt.close(fig)
            print(f"Generated plot: {path}")
        # else:
        #     print(f"Skipping {filename}: No non-zero data for {metric_key}.")

    # --- Response Size Plot ---
    avg_response_sizes = [float(libraries_data.get(lib_name, {}).get('workflow', {}).get('avg_response_size_bytes', 0) or 0) for lib_name in library_names]
    if any(s > 0 for s in avg_response_sizes):
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(library_names, avg_response_sizes, color=colors)
        ax.set_ylabel('Avg Response Size (Bytes)')
        ax.set_title('Average Telegram API Response Size (Lower is Better)')
        ax.tick_params(axis='x', rotation=45)
        add_labels(ax, unit=" B", format_spec=".1f") 
        fig.tight_layout()
        path = os.path.join(output_dir, 'plot_avg_response_size.png')
        plt.savefig(path)
        plot_paths['avg_response_size_bytes'] = os.path.basename(path)
        plt.close(fig)
        print(f"Generated plot: {path}")
    else:
         print(f"Skipping plot_avg_response_size.png: No positive data.")

    return plot_paths 