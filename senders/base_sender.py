from abc import ABC, abstractmethod
import time
import datetime # Import datetime module
import asyncio
import numpy as np # For percentile calculations
from benchmark_utils import ResourceMonitor # Import ResourceMonitor
from database_utils import get_sync_db_connection, read_message_sync, get_async_db_connection, read_message_async

class BaseSender(ABC):
    def __init__(self, token, chat_id, api_url_template, config_obj):
        self.token = token
        self.chat_id = chat_id
        self.api_url_template = api_url_template
        self.results = []
        self.library_name = self.__class__.__name__.replace("Sender", "")
        self.config = config_obj

    @abstractmethod
    def send_message_sync(self, db_conn, text_payload, message_params):
        """Synchronously sends a single message."""
        pass

    @abstractmethod
    async def initialize_session(self):
        """Initialize and return the network session/client object."""
        pass

    @abstractmethod
    async def close_session(self, session):
        """Close the network session/client object."""
        pass

    @abstractmethod
    async def send_message_async(self, session, db_conn, text_payload, message_params):
        """Asynchronously sends a single message using the provided session."""
        pass

    def _record_attempt(self, start_time, db_read_time_ms, response_status, response_text, response_size_bytes, success, error_message=None):
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        http_time_ms = total_time_ms - db_read_time_ms # Approximate HTTP time
        return {
            "status_code": response_status,
            "response_text_snippet": response_text[:100] if response_text else None,
            "response_size_bytes": response_size_bytes,
            "db_read_time_ms": round(db_read_time_ms, 2),
            "http_request_time_ms": round(http_time_ms, 2),
            "total_processing_time_ms": round(total_time_ms, 2),
            "success": success,
            "error_message": str(error_message) if error_message else None
        }

    def run_benchmark(self, num_messages, message_params=None):
        if message_params is None:
            # Default to no parse_mode for plain text, to avoid entity parsing errors with generated text
            message_params = {}

        run_details = []
        print(f"Benchmarking {self.library_name} ({self.get_sender_type()})...")

        monitor = ResourceMonitor(process_name_hint=f"{self.library_name}_sync_benchmark")
        monitor.start()

        # Synchronous execution path
        if self.get_sender_type() == "sync":
            try:
                with get_sync_db_connection() as db_conn:
                    for i in range(num_messages):
                        start_loop_time = time.perf_counter()
                        db_read_start_time = time.perf_counter()
                        # Fetch a row from DB to simulate a real workflow, but we'll generate payload on the fly
                        message_id, _ = read_message_sync(db_conn) # Original payload from DB ignored for sending
                        db_read_end_time = time.perf_counter()
                        db_read_time_ms = (db_read_end_time - db_read_start_time) * 1000

                        if message_id is None:
                            print(f"Warning: No more messages found in DB for run {i+1}. Stopping early for {self.library_name}.")
                            break
                        
                        # Generate unique message payload for this specific call
                        timestamp_str = datetime.datetime.now().strftime('%y%m%d_%H%M%S_%f')[:-3] # YYMMDD_HHMMSS_ms. No escaping needed for plain text.
                        actual_text_payload = f"{self.library_name} Test {timestamp_str}_{i+1}"

                        print(f"Sending message {i+1}/{num_messages} (DB ID: {message_id}, Lib: {self.library_name}) with content: '{actual_text_payload[:30]}...'")
                        try:
                            status, resp_text, resp_size, success = self.send_message_sync(db_conn, actual_text_payload, message_params)
                            # If send_message_sync returns success=False, resp_text might contain the error string
                            current_error_message = str(resp_text) if not success and resp_text else None
                            attempt_data = self._record_attempt(start_loop_time, db_read_time_ms, status, resp_text, resp_size, success, error_message=current_error_message)
                        except Exception as e:
                            # This exception is from BaseSender logic, or if send_message_sync raises unhandled
                            attempt_data = self._record_attempt(start_loop_time, db_read_time_ms, None, str(e), 0, False, error_message=str(e))
                        run_details.append(attempt_data)
                        # time.sleep(0.1) # Optional delay removed for now
            except Exception as e:
                print(f"FATAL ERROR during sync benchmark setup/DB connection for {self.library_name}: {e}")
                # No results to compile if DB connection fails
                monitor.stop() # Stop monitor even on failure
                return self._compile_summary([], monitor.get_results()) # Return empty summary

        else:
            raise TypeError(f"{self.library_name} is async, use run_benchmark_async method.")

        resource_usage = monitor.stop()
        return self._compile_summary(run_details, resource_usage)

    async def run_benchmark_async(self, num_messages, message_params=None):
        if message_params is None:
            # Default to no parse_mode for plain text
            message_params = {}

        run_details = []
        print(f"Benchmarking {self.library_name} ({self.get_sender_type()})...")
        
        monitor = ResourceMonitor(process_name_hint=f"{self.library_name}_async_benchmark")
        session = None
        resource_usage = {}
        
        try:
            monitor.start()
            session = await self.initialize_session()
            if not session:
                raise RuntimeError(f"Failed to initialize session for {self.library_name}")

            if self.get_sender_type() == "async":
                try:
                    async with get_async_db_connection() as db_conn:
                        for i in range(num_messages):
                            start_loop_time = time.perf_counter()
                            db_read_start_time = time.perf_counter()
                            # Fetch a row from DB to simulate a real workflow, but we'll generate payload on the fly
                            message_id, _ = await read_message_async(db_conn) # Original payload from DB ignored for sending
                            db_read_end_time = time.perf_counter()
                            db_read_time_ms = (db_read_end_time - db_read_start_time) * 1000

                            if message_id is None:
                                print(f"Warning: No more messages found in DB for run {i+1}. Stopping early for {self.library_name}.")
                                break
                            
                            # Generate unique message payload for this specific call
                            timestamp_str = datetime.datetime.now().strftime('%y%m%d_%H%M%S_%f')[:-3] # YYMMDD_HHMMSS_ms. No escaping needed for plain text.
                            actual_text_payload = f"{self.library_name} Test {timestamp_str}_{i+1}"

                            print(f"Sending message {i+1}/{num_messages} (DB ID: {message_id}, Lib: {self.library_name}) with content: '{actual_text_payload[:30]}...'")
                            try:
                                status, resp_text, resp_size, success = await self.send_message_async(session, db_conn, actual_text_payload, message_params)
                                # If send_message_async returns success=False, resp_text might contain the error string
                                current_error_message = str(resp_text) if not success and resp_text else None
                                attempt_data = self._record_attempt(start_loop_time, db_read_time_ms, status, resp_text, resp_size, success, error_message=current_error_message)
                            except Exception as e:
                                print(f"[ERROR in run_benchmark_async loop for {self.library_name}] Type: {type(e).__name__}, Error: {e}")
                                # This exception is from BaseSender logic, or if send_message_async raises unhandled
                                attempt_data = self._record_attempt(start_loop_time, db_read_time_ms, None, str(e), 0, False, error_message=str(e))
                            run_details.append(attempt_data)
                except Exception as e:
                    print(f"FATAL ERROR during async benchmark setup/DB connection for {self.library_name}: {e}")
                    monitor.stop()
                    return self._compile_summary([], monitor.get_results())
            else:
                raise TypeError(f"{self.library_name} is sync, use run_benchmark method.")

        except Exception as e:
            print(f"FATAL ERROR during async benchmark setup/run for {self.library_name}: {e}")
            if monitor.is_running():
                resource_usage = monitor.stop()
            else:
                resource_usage = monitor.get_results() if monitor.start_time else {}
            return self._compile_summary(run_details, resource_usage)
        finally:
            if monitor.is_running():
                resource_usage = monitor.stop()
            
            if session:
                try:
                    await self.close_session(session)
                except Exception as e_close:
                    print(f"Error closing session for {self.library_name}: {e_close}")
        
        return self._compile_summary(run_details, resource_usage)

    def _compile_summary(self, run_details, resource_usage_data):
        successful_requests = sum(1 for r in run_details if r["success"])
        failed_requests = len(run_details) - successful_requests
        total_attempts = len(run_details)
        success_rate_percent = (successful_requests / total_attempts * 100) if total_attempts > 0 else 0
        
        # Extract times for successful runs
        db_times = [r["db_read_time_ms"] for r in run_details if r["success"]]
        http_times = [r["http_request_time_ms"] for r in run_details if r["success"]]
        total_times = [r["total_processing_time_ms"] for r in run_details if r["success"]]
        response_sizes = [r["response_size_bytes"] for r in run_details if r["success"]]

        # Calculate stats (times in seconds for reporting consistency with example)
        avg_db_time_s = (sum(db_times) / len(db_times) / 1000) if db_times else 0
        avg_http_time_s = (sum(http_times) / len(http_times) / 1000) if http_times else 0
        avg_total_time_s = (sum(total_times) / len(total_times) / 1000) if total_times else 0

        p95_db_time_s = (np.percentile(db_times, 95) / 1000) if db_times else 0
        p99_db_time_s = (np.percentile(db_times, 99) / 1000) if db_times else 0
        p95_http_time_s = (np.percentile(http_times, 95) / 1000) if http_times else 0
        p99_http_time_s = (np.percentile(http_times, 99) / 1000) if http_times else 0
        p95_total_time_s = (np.percentile(total_times, 95) / 1000) if total_times else 0
        p99_total_time_s = (np.percentile(total_times, 99) / 1000) if total_times else 0

        # Standard Deviations
        std_db_time_s = (np.std(db_times) / 1000) if db_times else 0
        std_http_time_s = (np.std(http_times) / 1000) if http_times else 0
        std_total_time_s = (np.std(total_times) / 1000) if total_times else 0
        
        # Response Size
        avg_response_size = sum(response_sizes) / len(response_sizes) if response_sizes else 0

        # Throughput
        total_benchmark_duration_s = resource_usage_data.get("duration_seconds", 0)
        throughput = total_attempts / total_benchmark_duration_s if total_benchmark_duration_s > 0 else 0

        summary_data = {
            "library": self.library_name,
            "version": self.get_library_version(),
            "type": self.get_sender_type(),
            "run_details": run_details, # Detailed attempts
            "workflow": { 
                # Renaming fields slightly for clarity with DB inclusion
                "avg_db_read_time_s": round(avg_db_time_s, 5),
                "p95_db_read_time_s": round(p95_db_time_s, 5),
                "p99_db_read_time_s": round(p99_db_time_s, 5),
                "std_db_read_time_s": round(std_db_time_s, 5),
                "avg_http_send_time_s": round(avg_http_time_s, 5),
                "p95_http_send_time_s": round(p95_http_time_s, 5),
                "p99_http_send_time_s": round(p99_http_time_s, 5),
                "std_http_send_time_s": round(std_http_time_s, 5),
                "avg_total_processing_time_s": round(avg_total_time_s, 5),
                "p95_total_processing_time_s": round(p95_total_time_s, 5),
                "p99_total_processing_time_s": round(p99_total_time_s, 5),
                "std_total_processing_time_s": round(std_total_time_s, 5),
                "avg_response_size_bytes": round(avg_response_size, 1),
                "throughput_msg_per_sec": round(throughput, 2),
                
                "total_benchmark_duration_s": round(total_benchmark_duration_s, 4), # Overall time for this library's test
                
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