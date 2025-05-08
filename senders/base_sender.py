from abc import ABC, abstractmethod
import time
import asyncio

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

        return self._compile_summary(run_details)

    async def run_benchmark_async(self, num_messages, text_payload, message_params=None):
        if message_params is None:
            message_params = {'parse_mode': 'Markdown'}

        run_details = []
        print(f"Benchmarking {self.library_name} ({self.get_sender_type()})...")

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

        return self._compile_summary(run_details)

    def _compile_summary(self, run_details):
        successful_requests = sum(1 for r in run_details if r["success"])
        failed_requests = len(run_details) - successful_requests
        success_rate = (successful_requests / len(run_details) * 100) if len(run_details) > 0 else 0
        
        response_times = [r["response_time_ms"] for r in run_details if r["success"]]
        total_time_ms = sum(r["response_time_ms"] for r in run_details) # Sum of all attempts, incl. failures that took time

        summary = {
            "library": self.library_name,
            "type": self.get_sender_type(),
            "run_details": run_details,
            "summary": {
                "total_time_ms": round(total_time_ms, 2),
                "average_time_ms": round(sum(response_times) / len(response_times), 2) if response_times else 0,
                "min_time_ms": round(min(response_times), 2) if response_times else 0,
                "max_time_ms": round(max(response_times), 2) if response_times else 0,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate_percent": round(success_rate, 2),
                "cpu_usage_percent_avg": None,  # Placeholder
                "memory_increase_mb": None      # Placeholder
            }
        }
        return summary

    @abstractmethod
    def get_sender_type(self):
        """Returns 'sync' or 'async'."""
        pass

    def get_library_version(self):
        """Returns the version of the underlying HTTP library."""
        return "N/A" 