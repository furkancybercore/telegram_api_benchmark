import aiohttp
import asyncio
from .base_sender import BaseSender

class AiohttpSender(BaseSender):

    async def initialize_session(self):
        """Initialize and return the aiohttp ClientSession."""
        # Configure connector with limits from config
        connector = aiohttp.TCPConnector(limit=self.config.MAX_CONCURRENT_REQUESTS_PER_LIBRARY)
        # Configure timeout
        timeout = aiohttp.ClientTimeout(total=10.0)
        session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return session

    async def close_session(self, session: aiohttp.ClientSession):
        """Close the aiohttp ClientSession."""
        if session:
            await session.close()

    # Accepts session, db_conn, text_payload, message_params
    async def send_message_async(self, session: aiohttp.ClientSession, db_conn, text_payload, message_params):
        # Construct API URL using the template and token
        api_url = self.api_url_template.format(token=self.token)
        data = {
            'chat_id': self.chat_id,
            'text': text_payload,
            **message_params
        }
        response_size_bytes = 0
        response_text = ""
        try:
            # Use the passed-in session
            async with session.post(api_url, data=data) as response:
                response_body = await response.read() 
                response_size_bytes = len(response_body)
                try:
                    response_text = response_body.decode('utf-8')
                except UnicodeDecodeError:
                    response_text = "[Non-UTF8 Response Body]"
                
                # Check status after reading body
                success = 200 <= response.status < 300
                if not success:
                    print(f"[Debug {self.library_name}] HTTP Status Error: {response.status}, Response: {response_text[:200]}")
                    # raise_for_status() could be used earlier if body not needed on error
                
                return response.status, response_text, response_size_bytes, success
        except aiohttp.ClientResponseError as e:
            # Error captured by aiohttp (includes status code)
            error_text = getattr(e, 'message', str(e))
            print(f"[Debug {self.library_name}] ClientResponseError Status: {e.status}, Error: {error_text}, History: {e.history}")
            # Try to get response size if available (might be 0)
            return e.status, error_text, response_size_bytes, False
        except aiohttp.ClientError as e:
             # Other client errors (connection, etc.) - no status code typically
             error_text = str(e)
             print(f"[Debug {self.library_name}] ClientError: {error_text}")
             return 0, error_text, 0, False
        except asyncio.TimeoutError as e:
            print(f"[Debug {self.library_name}] TimeoutError: {e}")
            return 408, "Timeout Error", 0, False # Use 408 for timeout
        except Exception as e:
            print(f"[Debug {self.library_name}] General Error: Type={type(e).__name__}, Error={e}")
            return 500, str(e), 0, False

    def send_message_sync(self, db_conn, text_payload, message_params):
        raise NotImplementedError("aiohttp is an asynchronous library. Use send_message_async.")

    def get_sender_type(self):
        return "async"

    def get_library_version(self):
        return aiohttp.__version__ 