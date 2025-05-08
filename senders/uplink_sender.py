import uplink
from uplink import Body, Field, post, Consumer, headers
import aiohttp
import typing
from .base_sender import BaseSender

# Define the Telegram API consumer using Uplink
@headers({"Accept": "application/json", "Content-Type": "application/json"})
class TelegramUplinkService(Consumer):
    @post("sendMessage")
    async def send_telegram_message(self, payload: Body) -> typing.Any:
        """
        Sends a message via Telegram. The payload argument forms the JSON body.
        """
        pass

class UplinkSender(BaseSender):
    name = "uplink"
    _service: TelegramUplinkService = None
    _aiohttp_session: aiohttp.ClientSession = None

    async def initialize_session(self):
        self._aiohttp_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=self.config.MAX_CONCURRENT_REQUESTS_PER_LIBRARY)
        )
        if not self.config.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in config.")
        base_api_url = f"https://api.telegram.org/bot{self.config.TELEGRAM_BOT_TOKEN}/"
        self._service = uplink.builder.build(
            TelegramUplinkService, 
            base_url=base_api_url, 
            client=self._aiohttp_session
        )
        return self._aiohttp_session

    async def close_session(self, session: aiohttp.ClientSession):
        if session:
            await session.close()
        self._service = None
        self._aiohttp_session = None

    async def send_message_async(self, 
                                 session: aiohttp.ClientSession,
                                 db_conn, 
                                 text_payload: str, 
                                 message_params: dict):
        if not self._service:
            if session != self._aiohttp_session:
                 print(f"[Warning {self.name}] Session mismatch detected!")
            raise RuntimeError("Uplink service not initialized. Call initialize_session first.")
        
        call_kwargs = {
            "chat_id": self.chat_id,
            "text": text_payload
        }
        if message_params:
            call_kwargs.update(message_params)

        try:
            uplink_response: aiohttp.ClientResponse = await self._service.send_telegram_message(payload=call_kwargs)
            
            status_code = uplink_response.status
            response_body_bytes = await uplink_response.read()
            response_text = response_body_bytes.decode('utf-8', errors='replace')
            response_size = len(response_body_bytes)
            success = 200 <= status_code < 300
            if not success:
                 print(f"[Debug {self.name}] Non-2xx Success Status: {status_code}, Response: {response_text[:200]}")
            return status_code, response_text, response_size, success
        except aiohttp.ClientResponseError as e:
            status = e.status
            error_text = e.message + (f" | Response: {e.response_text[:100]}" if hasattr(e, 'response_text') else "")
            print(f"{self.name} sender aiohttp.ClientResponseError: {status} - {e.message}")
            print(f"[Debug {self.name}] aiohttp.ClientResponseError Status: {status}, Message: {e.message}, Headers: {e.headers}")
            return status, error_text, 0, False
        except aiohttp.ClientConnectionError as e:
            status = 0
            error_text = str(e)
            print(f"{self.name} sender aiohttp.ClientConnectionError: {error_text}")
            return status, error_text, 0, False
        except aiohttp.ClientError as e:
            status = e.status if hasattr(e, 'status') else 0
            error_text = str(e)
            print(f"{self.name} sender aiohttp.ClientError: {error_text}")
            print(f"[Debug {self.name}] aiohttp.ClientError Status: {status}, Error: {error_text}")
            return status, error_text, 0, False
        except Exception as e:
            status = 500
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                status = e.response.status_code
            elif hasattr(e, 'status_code'):
                status = e.status_code
            error_text = str(e)
            print(f"{self.name} sender general error: {e}")
            print(f"[Debug {self.name}] General Error Status: {status}, Type: {type(e).__name__}, Error: {error_text}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                 print(f"[Debug {self.name}] General Error Response Hint: {e.response.text[:200]}")
            return status, error_text, 0, False

    def send_message_sync(self, db_conn, text_payload, message_params):
        raise NotImplementedError(f"{self.name} is implemented as asynchronous only.")

    def get_sender_type(self):
        return "async"

    def get_library_version(self):
        try:
            import uplink as u_pkg
            return u_pkg.__version__
        except ImportError:
            return "uplink (version not found)" 