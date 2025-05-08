import urllib3
import json # For encoding the payload
from .base_sender import BaseSender

class Urllib3Sender(BaseSender):
    def __init__(self, token, chat_id, api_url_template):
        super().__init__(token, chat_id, api_url_template)
        # Create a PoolManager instance. Consider if timeout/retries need adjustment.
        self.http = urllib3.PoolManager()

    def send_message_sync(self, db_conn, text_payload, message_params):
        data = {
            'chat_id': self.chat_id,
            'text': text_payload,
            **message_params
        }
        response_size_bytes = 0
        response_text = ""
        try:
            response = self.http.request(
                "POST",
                self.api_url,
                fields=data, # Encodes as multipart/form-data
                timeout=urllib3.Timeout(total=10.0)
            )
            response_size_bytes = len(response.data)
            # Decode assuming UTF-8, handle potential errors
            try:
                response_text = response.data.decode('utf-8')
            except UnicodeDecodeError:
                response_text = "[Non-UTF8 Response Body]"

            if 200 <= response.status < 300:
                return response.status, response_text, response_size_bytes, True
            else:
                # Return body/size even on failure if available
                return response.status, response_text, response_size_bytes, False
        except urllib3.exceptions.MaxRetryError as e:
            return None, str(e), 0, False
        except urllib3.exceptions.TimeoutError:
            return None, "Timeout Error", 0, False
        except urllib3.exceptions.HTTPError as e:
            return None, str(e), 0, False
        except Exception as e:
            return None, str(e), 0, False

    async def send_message_async(self, db_conn, text_payload, message_params):
        raise NotImplementedError("urllib3 in this context is used synchronously. Async version not implemented here.")

    def get_sender_type(self):
        return "sync"

    def get_library_version(self):
        return urllib3.__version__ 