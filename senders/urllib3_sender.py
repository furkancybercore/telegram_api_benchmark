import urllib3
import json # For encoding the payload
from .base_sender import BaseSender

class Urllib3Sender(BaseSender):
    def __init__(self, token, chat_id, api_url_template):
        super().__init__(token, chat_id, api_url_template)
        # Create a PoolManager instance for making requests.
        self.http = urllib3.PoolManager()

    def send_message_sync(self, text_payload, message_params):
        data = {
            'chat_id': self.chat_id,
            'text': text_payload,
            **message_params
        }
        try:
            # urllib3 expects bytes for the body if not form-encoded with fields
            # For JSON payload, it would be json.dumps(data).encode('utf-8') and Content-Type: application/json
            # For Telegram, it's typically x-www-form-urlencoded or multipart/form-data.
            # PoolManager.request handles form-encoding if `fields` is a dict.
            response = self.http.request(
                "POST",
                self.api_url,
                fields=data, # This will encode as multipart/form-data by default
                timeout=urllib3.Timeout(total=10.0)
            )
            response_data = response.data.decode('utf-8')
            if 200 <= response.status < 300:
                return response.status, response_data[:100], True
            else:
                return response.status, response_data[:100], False
        except urllib3.exceptions.MaxRetryError as e:
            # This can wrap other errors like NewConnectionError, TimeoutError
            return None, str(e), False
        except urllib3.exceptions.TimeoutError:
            return None, "Timeout Error", False
        except urllib3.exceptions.HTTPError as e:
            # General HTTP errors
            return None, str(e), False
        except Exception as e:
            return None, str(e), False

    async def send_message_async(self, text_payload, message_params):
        # urllib3 is primarily a synchronous library. Async support is newer and might require different setup.
        # For simplicity, marking this as not implemented for typical urllib3 usage.
        raise NotImplementedError("urllib3 in this context is used synchronously. Async version not implemented here.")

    def get_sender_type(self):
        return "sync"

    def get_library_version(self):
        return urllib3.__version__ 