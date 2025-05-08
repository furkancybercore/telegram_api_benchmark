import requests
from .base_sender import BaseSender

class RequestsSender(BaseSender):
    def __init__(self, token, chat_id, api_url_template, config_obj):
        super().__init__(token, chat_id, api_url_template, config_obj)
        self.api_url = self.api_url_template.format(token=self.token) # Initialize api_url

    async def initialize_session(self):
        # Requests manages sessions per-request or via a Session object,
        # but for this benchmark structure, we don't need to pre-initialize one globally.
        return None # Or self, doesn't strictly matter for sync sender

    async def close_session(self, session):
        # No explicit session to close that was managed by initialize_session
        pass

    def send_message_sync(self, db_conn, text_payload, message_params):
        data = {
            'chat_id': self.chat_id,
            'text': text_payload,
            **message_params
        }
        response_size_bytes = 0
        response_text = ""
        try:
            response = requests.post(self.api_url, data=data, timeout=10) 
            response_size_bytes = len(response.content) # Get size from content bytes
            response_text = response.text # Access text after size
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            return response.status_code, response_text, response_size_bytes, True
        except requests.exceptions.HTTPError as e:
            # Ensure response text/size are captured even on HTTP error
            if e.response is not None:
                 response_size_bytes = len(e.response.content)
                 response_text = e.response.text
                 return e.response.status_code, response_text, response_size_bytes, False
            else:
                 return None, str(e), 0, False # No response object available
        except requests.exceptions.RequestException as e:
            return None, str(e), 0, False
        except Exception as e:
            return None, str(e), 0, False

    async def send_message_async(self, db_conn, text_payload, message_params):
        raise NotImplementedError("requests is a synchronous library. Use send_message_sync.")

    def get_sender_type(self):
        return "sync"

    def get_library_version(self):
        return requests.__version__ 