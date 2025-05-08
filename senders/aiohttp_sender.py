import aiohttp
import asyncio
from .base_sender import BaseSender

class AiohttpSender(BaseSender):
    async def send_message_async(self, db_conn, text_payload, message_params):
        data = {
            'chat_id': self.chat_id,
            'text': text_payload,
            **message_params
        }
        response_size_bytes = 0
        response_text = ""
        try:
            # Create a single session for the benchmark run if possible (passed or managed)
            # For simplicity here, creating per request. Consider pooling in main/base for real apps.
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.post(self.api_url, data=data) as response:
                    # Read the response body to get size and text
                    response_body = await response.read() 
                    response_size_bytes = len(response_body)
                    # Decode assuming UTF-8, handle potential errors
                    try:
                        response_text = response_body.decode('utf-8')
                    except UnicodeDecodeError:
                        response_text = "[Non-UTF8 Response Body]"
                    
                    if response.status >= 400:
                        # Raise for status might be cleaner if we don't need the body on error
                        # response.raise_for_status() 
                        return response.status, response_text, response_size_bytes, False
                    return response.status, response_text, response_size_bytes, True
        except aiohttp.ClientResponseError as e:
            # Error body/size might be accessible via e.message or history depending on aiohttp version/error type
             return e.status, getattr(e, 'message', str(e)), response_size_bytes, False
        except aiohttp.ClientError as e:
            return None, str(e), 0, False
        except asyncio.TimeoutError:
            return None, "Timeout Error", 0, False
        except Exception as e:
            return None, str(e), 0, False

    def send_message_sync(self, db_conn, text_payload, message_params):
        raise NotImplementedError("aiohttp is an asynchronous library. Use send_message_async.")

    def get_sender_type(self):
        return "async"

    def get_library_version(self):
        return aiohttp.__version__ 