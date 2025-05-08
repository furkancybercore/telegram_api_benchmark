import aiohttp
import asyncio
from .base_sender import BaseSender

class AiohttpSender(BaseSender):
    async def send_message_async(self, text_payload, message_params):
        data = {
            'chat_id': self.chat_id,
            'text': text_payload,
            **message_params
        }
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.post(self.api_url, data=data) as response:
                    resp_text = await response.text()
                    # aiohttp raises ClientResponseError for 4xx/5xx if raise_for_status() is called
                    # or we can check response.status manually
                    if response.status >= 400:
                        return response.status, resp_text[:100], False
                    return response.status, resp_text[:100], True
        except aiohttp.ClientError as e:
            # Covers various client-side errors like connection issues, timeouts
            return None, str(e), False
        except asyncio.TimeoutError:
            return None, "Timeout Error", False # Explicitly catch asyncio.TimeoutError
        except Exception as e:
            return None, str(e), False

    def send_message_sync(self, text_payload, message_params):
        # aiohttp is async-only
        raise NotImplementedError("aiohttp is an asynchronous library. Use send_message_async.")

    def get_sender_type(self):
        return "async"

    def get_library_version(self):
        return aiohttp.__version__ 