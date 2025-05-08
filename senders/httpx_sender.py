import httpx
import asyncio
from .base_sender import BaseSender

class HttpxSender(BaseSender):
    
    async def initialize_session(self):
        """Initialize and return the httpx AsyncClient."""
        # Use configured concurrency limits if applicable (httpx uses httpcore limits)
        # We can configure limits on the transport.
        limits = httpx.Limits(max_connections=self.config.MAX_CONCURRENT_REQUESTS_PER_LIBRARY, 
                              max_keepalive_connections=20) # Default keepalive
        timeout = httpx.Timeout(10.0, connect=5.0)
        transport = httpx.AsyncHTTPTransport(limits=limits, retries=1) 
        client = httpx.AsyncClient(transport=transport, timeout=timeout, http2=True) # Enable HTTP/2
        return client

    async def close_session(self, session: httpx.AsyncClient):
        """Close the httpx AsyncClient."""
        if session:
            await session.aclose()

    # Accepts session, db_conn, text_payload, message_params
    async def send_message_async(self, session: httpx.AsyncClient, db_conn, text_payload, message_params):
        # Construct API URL using the template and token
        api_url = self.api_url_template.format(token=self.token)
        data = {
            'chat_id': self.chat_id,
            'text': text_payload,
            **message_params
        }
        try:
            # Use the passed-in session client
            response = await session.post(api_url, data=data) # Timeout is set on client
            response.raise_for_status() 
            response_text = response.text
            response_size_bytes = len(response.content)
            return response.status_code, response_text, response_size_bytes, True
        except httpx.HTTPStatusError as e:
            response_text = e.response.text
            response_size_bytes = len(e.response.content)
            # Add debug log
            print(f"[Debug {self.library_name}] HTTP Status Error: {e.response.status_code}, Response: {response_text[:200]}")
            return e.response.status_code, response_text, response_size_bytes, False
        except httpx.RequestError as e:
            # Add debug log
            print(f"[Debug {self.library_name}] Request Error: {e}")
            return 0, str(e), 0, False # Use 0 for status code on connection errors
        except Exception as e:
            # Add debug log
            print(f"[Debug {self.library_name}] General Error: Type={type(e).__name__}, Error={e}")
            return 500, str(e), 0, False # Use 500 for unknown errors

    def send_message_sync(self, db_conn, text_payload, message_params):
        # This sync version is primarily a placeholder if needed, focus is async
        api_url = self.api_url_template.format(token=self.token)
        data = {
            'chat_id': self.chat_id,
            'text': text_payload,
            **message_params
        }
        try:
            with httpx.Client() as client:
                response = client.post(api_url, data=data, timeout=10.0)
                response.raise_for_status()
                response_text = response.text
                response_size_bytes = len(response.content)
                return response.status_code, response_text, response_size_bytes, True
        except httpx.HTTPStatusError as e:
            response_text = e.response.text
            response_size_bytes = len(e.response.content)
            return e.response.status_code, response_text, response_size_bytes, False
        except httpx.RequestError as e:
            return 0, str(e), 0, False
        except Exception as e:
            return 500, str(e), 0, False

    def get_sender_type(self):
        return "async" # Primary focus is async

    def get_library_version(self):
        return httpx.__version__ 