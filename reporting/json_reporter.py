import json
import os
import datetime
import platform
import sys

def generate_report(data, output_dir, filename):
    """Generates a JSON report from the benchmark data."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    report_path = os.path.join(output_dir, filename)
    
    # Enhance data with more benchmark details if not already present
    # Some of this might be pre-filled by main.py
    if "benchmark_details" not in data:
        data["benchmark_details"] = {}
    
    data["benchmark_details"].update({
        "report_generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        # Library versions should be added by main.py from each sender
    })

    try:
        with open(report_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"JSON report generated: {report_path}")
    except IOError as e:
        print(f"Error writing JSON report to {report_path}: {e}")
    except TypeError as e:
        print(f"Error serializing data to JSON: {e}. Data: {data}") 