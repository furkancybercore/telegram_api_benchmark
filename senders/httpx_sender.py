import httpx
import asyncio
from .base_sender import BaseSender

class HttpxSender(BaseSender):
    async def send_message_async(self, text_payload, message_params):
        data = {
            'chat_id': self.chat_id,
            'text': text_payload,
            **message_params
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.api_url, data=data, timeout=10.0) # 10s timeout
                response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
                return response.status_code, response.text[:100], True # Return first 100 chars of response
        except httpx.HTTPStatusError as e:
            return e.response.status_code, e.response.text[:100], False
        except httpx.RequestError as e:
            # For network errors, timeout, etc.
            return None, str(e), False
        except Exception as e:
            return None, str(e), False

    def send_message_sync(self, text_payload, message_params):
        # httpx can also be used synchronously if needed, but we focus on async for this class
        # For a purely sync version, one might create HttpxSyncSender(BaseSender)
        # This is a placeholder if BaseSender strictly requires it.
        # Alternatively, make send_message_sync optional or raise NotImplementedError.
        # For now, let's implement a basic sync version as well.
        data = {
            'chat_id': self.chat_id,
            'text': text_payload,
            **message_params
        }
        try:
            with httpx.Client() as client:
                response = client.post(self.api_url, data=data, timeout=10.0)
                response.raise_for_status()
                return response.status_code, response.text[:100], True
        except httpx.HTTPStatusError as e:
            return e.response.status_code, e.response.text[:100], False
        except httpx.RequestError as e:
            return None, str(e), False
        except Exception as e:
            return None, str(e), False

    def get_sender_type(self):
        return "async" # Primary focus is async for httpx in this comparison

    def get_library_version(self):
        return httpx.__version__ 