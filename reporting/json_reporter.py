import json
import os
import datetime
import platform
import sys

def generate_report(data, output_dir, filename):
    """Generates a JSON report from the benchmark data.
    Expects data to have a 'benchmark_details' key and a 'libraries' key,
    where 'libraries' is a dictionary of library-specific results.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    report_path = os.path.join(output_dir, filename)
    
    # Ensure basic benchmark details are present, though main.py should provide most of these
    if "benchmark_details" not in data:
        data["benchmark_details"] = {}
    
    # These are typically already set by main.py but ensure they are present.
    data["benchmark_details"].setdefault("report_generated_at", datetime.datetime.now(datetime.timezone.utc).isoformat())
    data["benchmark_details"].setdefault("python_version", platform.python_version())
    data["benchmark_details"].setdefault("platform", platform.platform())
    # 'libraries_versions' and 'parameters' should be populated by main.py within benchmark_details

    # The main data under "libraries" should already be structured correctly by main.py

    try:
        with open(report_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"JSON report generated: {report_path}")
    except IOError as e:
        print(f"Error writing JSON report to {report_path}: {e}")
    except TypeError as e:
        print(f"Error serializing data to JSON: {e}. Ensure all data is JSON serializable. Problematic data: {data}") 