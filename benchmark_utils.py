import psutil
import time
import os

class ResourceMonitor:
    """A simple class to monitor CPU and memory usage."""
    def __init__(self, process_name_hint="benchmark_process"):
        self.process = psutil.Process(os.getpid())
        self.process_name_hint = process_name_hint # For logging/labeling if needed
        self.cpu_time_start = 0
        self.memory_start_mb = 0
        self.duration_seconds = 0
        self._monitoring_start_time = 0
        self._is_running = False # Add a flag

    def start(self):
        """Start monitoring resources."""
        self.process.cpu_percent(interval=None) # Initialize CPU tracking
        self.cpu_time_start = self.process.cpu_times().user + self.process.cpu_times().system
        self.memory_start_mb = self.process.memory_info().rss / (1024 * 1024) # Convert bytes to MB
        self._monitoring_start_time = time.perf_counter()
        self._is_running = True # Set flag to true
        print(f"Resource monitor started for '{self.process_name_hint}'. Initial Mem: {self.memory_start_mb:.2f} MB")

    def stop(self):
        """Stop monitoring and calculate usage."""
        if not self._is_running: # Prevent stopping if not started
            # print(f"Warning: Resource monitor for '{self.process_name_hint}' was asked to stop but was not running.")
            return self.get_results() # Or return None/empty dict if preferred

        self._monitoring_end_time = time.perf_counter()
        self.duration_seconds = self._monitoring_end_time - self._monitoring_start_time
        self._is_running = False # Set flag to false
        
        # CPU
        cpu_time_end = self.process.cpu_times().user + self.process.cpu_times().system
        total_cpu_time_spent = cpu_time_end - self.cpu_time_start
        
        # Calculate CPU percentage over the duration
        # psutil.cpu_count() gives logical CPUs, which is what cpu_percent usually considers for system-wide
        # For a single process, this calculation is a bit different than system-wide psutil.cpu_percent()
        # It aims to reflect how much CPU time this process used during its run, spread over the interval.
        if self.duration_seconds > 0:
            # Percentage of one core's time. Can be > 100% if multi-threaded and using multiple cores.
            self.cpu_time_percent = (total_cpu_time_spent / self.duration_seconds) * 100
        else:
            self.cpu_time_percent = 0

        # Memory
        memory_end_mb = self.process.memory_info().rss / (1024 * 1024)
        self.memory_increase_mb = memory_end_mb - self.memory_start_mb

        print(f"Resource monitor stopped for '{self.process_name_hint}'. Duration: {self.duration_seconds:.2f}s, Final Mem: {memory_end_mb:.2f} MB, Increase: {self.memory_increase_mb:.2f} MB, CPU Time Percent: {self.cpu_time_percent:.2f}%")
        return self.get_results()

    def get_results(self):
        """Return a dictionary of the collected resource usage."""
        return {
            "label": self.process_name_hint,
            "duration_seconds": round(self.duration_seconds, 4),
            "cpu_time_percent": round(self.cpu_time_percent, 2),
            "memory_start_mb": round(self.memory_start_mb, 2),
            "memory_end_mb": round(self.process.memory_info().rss / (1024 * 1024), 2), # Get current end MB
            "memory_increase_mb": round(self.memory_increase_mb, 2),
            "timestamp": time.time() # Current timestamp for when results are fetched
        }
    
    def is_running(self): # Add the new method
        """Check if the monitor is currently running."""
        return self._is_running 