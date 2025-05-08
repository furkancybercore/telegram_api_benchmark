import requests
from .base_sender import BaseSender

class RequestsSender(BaseSender):
    def send_message_sync(self, text_payload, message_params):
        data = {
            'chat_id': self.chat_id,
            'text': text_payload,
            **message_params
        }
        try:
            response = requests.post(self.api_url, data=data, timeout=10) # 10s timeout
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            return response.status_code, response.text[:100], True
        except requests.exceptions.HTTPError as e:
            # Error from server (4xx, 5xx)
            return e.response.status_code, e.response.text[:100], False
        except requests.exceptions.RequestException as e:
            # Other request errors (timeout, connection error, etc.)
            return None, str(e), False
        except Exception as e:
            return None, str(e), False

    async def send_message_async(self, text_payload, message_params):
        # requests is a synchronous library
        raise NotImplementedError("requests is a synchronous library. Use send_message_sync.")

    def get_sender_type(self):
        return "sync"

    def get_library_version(self):
        return requests.__version__ 