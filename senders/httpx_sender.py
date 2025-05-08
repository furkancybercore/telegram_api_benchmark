import httpx
import asyncio
from .base_sender import BaseSender

class HttpxSender(BaseSender):
    # Accepts db_conn, but doesn't use it directly here, it's used by run_benchmark_async
    async def send_message_async(self, db_conn, text_payload, message_params):
        data = {
            'chat_id': self.chat_id,
            'text': text_payload,
            **message_params
        }
        try:
            # Reuse the client for potential connection pooling benefits if needed
            # For this simple case, creating a new client per request is fine
            async with httpx.AsyncClient() as client:
                response = await client.post(self.api_url, data=data, timeout=10.0) 
                response.raise_for_status() 
                response_text = response.text # Read text before getting size
                response_size_bytes = len(response.content) # Get size from content bytes
                return response.status_code, response_text, response_size_bytes, True
        except httpx.HTTPStatusError as e:
            response_text = e.response.text
            response_size_bytes = len(e.response.content)
            return e.response.status_code, response_text, response_size_bytes, False
        except httpx.RequestError as e:
            return None, str(e), 0, False
        except Exception as e:
            return None, str(e), 0, False

    def send_message_sync(self, db_conn, text_payload, message_params):
        # This sync version is primarily a placeholder if needed, focus is async
        data = {
            'chat_id': self.chat_id,
            'text': text_payload,
            **message_params
        }
        try:
            with httpx.Client() as client:
                response = client.post(self.api_url, data=data, timeout=10.0)
                response.raise_for_status()
                response_text = response.text
                response_size_bytes = len(response.content)
                return response.status_code, response_text, response_size_bytes, True
        except httpx.HTTPStatusError as e:
            response_text = e.response.text
            response_size_bytes = len(e.response.content)
            return e.response.status_code, response_text, response_size_bytes, False
        except httpx.RequestError as e:
            return None, str(e), 0, False
        except Exception as e:
            return None, str(e), 0, False

    def get_sender_type(self):
        return "async" # Primary focus is async

    def get_library_version(self):
        return httpx.__version__ 