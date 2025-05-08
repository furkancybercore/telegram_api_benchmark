import uplink
from uplink import Consumer, get, post, Field, form_url_encoded
import aiohttp
import typing
import json
from .base_sender import BaseSender

# Define the Telegram API consumer using Uplink
class TelegramAPI(Consumer):
    """A simple Telegram Bot API client."""
    
    # Use form_url_encoded for Telegram API which works well with standard form data
    @form_url_encoded
    @post("sendMessage")
    def send_message(self, 
                    chat_id: Field, 
                    text: Field) -> aiohttp.ClientResponse:
        """Send a message to a chat."""
        pass

class UplinkSender(BaseSender):
    name = "uplink"
    
    async def initialize_session(self):
        """Initialize the aiohttp session and Uplink service."""
        self._aiohttp_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=self.config.MAX_CONCURRENT_REQUESTS_PER_LIBRARY)
        )
        
        # Build the Telegram API client with the base URL including the token
        base_url = f"https://api.telegram.org/bot{self.token}/"
        self._api = uplink.build(TelegramAPI, base_url=base_url, client=self._aiohttp_session)
        
        return self._aiohttp_session
    
    async def close_session(self, session):
        """Close the aiohttp session."""
        if session and not session.closed:
            await session.close()
        self._api = None
        self._aiohttp_session = None
    
    async def send_message_async(self, 
                               session,
                               db_conn, 
                               text_payload, 
                               message_params):
        """Send a message using the Uplink client."""
        if not self._api:
            raise RuntimeError("API client not initialized")
        
        try:
            # Use a simple form call which matches Telegram's expectations
            response = await self._api.send_message(
                chat_id=self.chat_id,
                text=text_payload
            )
            
            # Process the response 
            status_code = response.status
            content_bytes = await response.read()
            response_text = content_bytes.decode('utf-8', errors='replace')
            response_size = len(content_bytes)
            success = 200 <= status_code < 300
            
            return status_code, response_text, response_size, success
            
        except aiohttp.ClientResponseError as e:
            return e.status, str(e), 0, False
            
        except aiohttp.ClientError as e:
            return 0, str(e), 0, False
            
        except Exception as e:
            return 0, str(e), 0, False

    def send_message_sync(self, db_conn, text_payload, message_params):
        """Send a message using Uplink in synchronous mode.
        This implementation doesn't use the Uplink client directly as it's designed for async,
        but falls back to a simple requests implementation for sync operations."""
        import requests
        
        # Format the URL directly
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        
        # Prepare the form data
        data = {
            'chat_id': self.chat_id,
            'text': text_payload
        }
        
        # Add any additional parameters
        if message_params:
            data.update(message_params)
        
        try:
            # Use requests directly for sync operations
            response = requests.post(url, data=data, timeout=10)
            status_code = response.status_code
            response_text = response.text
            response_size = len(response.content)
            success = 200 <= status_code < 300
            
            return status_code, response_text, response_size, success
            
        except requests.RequestException as e:
            return 0, str(e), 0, False
            
        except Exception as e:
            return 0, str(e), 0, False

    def get_sender_type(self):
        return "async"  # Primary mode is async

    def get_library_version(self):
        return uplink.__version__ 