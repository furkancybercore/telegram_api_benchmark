from abc import ABC, abstractmethod
import time
import asyncio
from benchmark_utils import ResourceMonitor # Import ResourceMonitor

class BaseSender(ABC):
    def __init__(self, token, chat_id, api_url_template):
        self.token = token
        self.chat_id = chat_id
        self.api_url = api_url_template.format(token=self.token)
        self.results = []
        self.library_name = self.__class__.__name__.replace("Sender", "")

    @abstractmethod
    def send_message_sync(self, text_payload, message_params):
        """Synchronously sends a single message."""
        pass

    @abstractmethod
    async def send_message_async(self, text_payload, message_params):
        """Asynchronously sends a single message."""
        pass

    def _record_attempt(self, start_time, response_status, response_text, success, error_message=None):
        end_time = time.perf_counter()
        response_time_ms = (end_time - start_time) * 1000
        return {
            "status_code": response_status,
            "response_text": response_text, # Store part of response for debugging
            "response_time_ms": round(response_time_ms, 2),
            "success": success,
            "error_message": str(error_message) if error_message else None
        }

    def run_benchmark(self, num_messages, text_payload, message_params=None):
        if message_params is None:
            message_params = {'parse_mode': 'Markdown'}

        run_details = []
        print(f"Benchmarking {self.library_name} ({self.get_sender_type()})...")

        monitor = ResourceMonitor(process_name_hint=f"{self.library_name}_sync_benchmark")
        monitor.start()

        # Synchronous execution path
        if self.get_sender_type() == "sync":
            for i in range(num_messages):
                print(f"Sending message {i+1}/{num_messages} using {self.library_name}...")
                start_time = time.perf_counter()
                try:
                    status, resp_text, success = self.send_message_sync(text_payload, message_params)
                    attempt_data = self._record_attempt(start_time, status, resp_text, success)
                except Exception as e:
                    attempt_data = self._record_attempt(start_time, None, None, False, e)
                run_details.append(attempt_data)
                time.sleep(0.1) # Small delay to avoid overwhelming the API too quickly

        # Asynchronous execution path must be handled by main.py using asyncio.run()
        # This method should not be directly called for async senders here
        # Instead, an async version like `run_benchmark_async` will be called from main

        resource_usage = monitor.stop()
        return self._compile_summary(run_details, resource_usage)

    async def run_benchmark_async(self, num_messages, text_payload, message_params=None):
        if message_params is None:
            message_params = {'parse_mode': 'Markdown'}

        run_details = []
        print(f"Benchmarking {self.library_name} ({self.get_sender_type()})...")
        
        monitor = ResourceMonitor(process_name_hint=f"{self.library_name}_async_benchmark")
        monitor.start()

        if self.get_sender_type() == "async":
            for i in range(num_messages):
                print(f"Sending message {i+1}/{num_messages} using {self.library_name}...")
                start_time = time.perf_counter()
                try:
                    status, resp_text, success = await self.send_message_async(text_payload, message_params)
                    attempt_data = self._record_attempt(start_time, status, resp_text, success)
                except Exception as e:
                    attempt_data = self._record_attempt(start_time, None, None, False, e)
                run_details.append(attempt_data)
                await asyncio.sleep(0.1) # Small delay for async too
        else:
            # Should not happen if called correctly
            raise TypeError(f"{self.library_name} is sync, use run_benchmark method.")

        resource_usage = monitor.stop()
        return self._compile_summary(run_details, resource_usage)

    def _compile_summary(self, run_details, resource_usage_data):
        successful_requests = sum(1 for r in run_details if r["success"])
        failed_requests = len(run_details) - successful_requests
        total_attempts = len(run_details)
        success_rate_percent = (successful_requests / total_attempts * 100) if total_attempts > 0 else 0
        
        successful_response_times_ms = [r["response_time_ms"] for r in run_details if r["success"]]
        
        # Calculate total time for all requests (including failures that took time) in seconds
        total_run_time_ms = sum(r["response_time_ms"] for r in run_details)
        total_run_time_s = round(total_run_time_ms / 1000, 4)

        avg_response_time_ms = sum(successful_response_times_ms) / len(successful_response_times_ms) if successful_response_times_ms else 0
        min_response_time_ms = min(successful_response_times_ms) if successful_response_times_ms else 0
        max_response_time_ms = max(successful_response_times_ms) if successful_response_times_ms else 0

        # Metrics for "workflow" - aligning with the example report
        # In our current single-action benchmark, "telegram send time" is the main metric.
        # "avg_workflow_run_time" would be the same as "avg_telegram_send_time" if workflow is just one send.
        # If NUM_MESSAGES > 1, total_run_time_s is the time for all messages for this library.
        avg_telegram_send_time_s = round(avg_response_time_ms / 1000, 4)

        summary_data = {
            "library": self.library_name,
            "version": self.get_library_version(), # Store version here
            "type": self.get_sender_type(),
            "run_details": run_details, # Detailed attempts
            "workflow": { # Aligning with the structure of the example report
                "avg_telegram_send_time_s": avg_telegram_send_time_s,
                "min_telegram_send_time_s": round(min_response_time_ms / 1000, 4),
                "max_telegram_send_time_s": round(max_response_time_ms / 1000, 4),
                "total_workflow_time_all_runs_s": total_run_time_s, # Total time for all NUM_MESSAGES
                # "avg_workflow_run_time_s": avg_telegram_send_time_s, # If workflow = single send
                "successful_runs": successful_requests,
                "failed_runs": failed_requests,
                "total_runs": total_attempts,
                "success_rate_percent": round(success_rate_percent, 2),
                "cpu_time_percent": resource_usage_data.get("cpu_time_percent"),
                "memory_increase_mb": resource_usage_data.get("memory_increase_mb")
            }
        }
        return summary_data

    @abstractmethod
    def get_sender_type(self):
        """Returns 'sync' or 'async'."""
        pass

    def get_library_version(self):
        """Returns the version of the underlying HTTP library."""
        return "N/A" 