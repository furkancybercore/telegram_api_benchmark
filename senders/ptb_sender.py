from telegram import Bot
from telegram.error import TelegramError, BadRequest, TimedOut, NetworkError
# from telegram.request import HTTPXRequest # Not strictly needed for default PTB usage
import json

from .base_sender import BaseSender # Removed PerformanceStats

class PTBSender(BaseSender):
    name = "python-telegram-bot"
    _bot: Bot = None

    async def initialize_session(self):
        if not self.config.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in config for PTBSender.")
        self._bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)
        await self._bot.initialize()
        return self._bot # BaseSender expects the session object to be returned

    async def close_session(self, session: Bot):
        if session: # session is self._bot
            await session.shutdown()
        self._bot = None

    async def send_message_async(self, 
                                 session: Bot, # Add session parameter
                                 db_conn, # Ignored by this sender
                                 text_payload: str, 
                                 message_params: dict # Ignored by this sender
                                 ) -> tuple[int, str, int, bool]: # Corrected return signature
        """Sends a message using the initialized PTB Bot."""
        # session argument is present to match BaseSender, but self._bot is used internally.
        if not self._bot:
            raise RuntimeError("PTB Bot not initialized. Call initialize_session first.")

        # PTB's send_message uses text_payload directly.
        # The (ID: {message_id}) formatting is removed for consistency.
        api_payload_text = text_payload
        
        try:
            sent_message = await self._bot.send_message(chat_id=self.chat_id, text=api_payload_text)
            
            status_code = 200 # Inferred on success
            response_body_str = sent_message.to_json() # PTB Message object to JSON string
            response_body_bytes = response_body_str.encode('utf-8')
            response_size = len(response_body_bytes)
            success = True # If no exception, assume success
            
            return status_code, response_body_str, response_size, success

        except BadRequest as e:
            # Specific logging for PTB errors
            error_desc = e.message
            error_code = 400 # Assume 400 for BadRequest
            print(f"{self.name} sender BadRequest: {error_desc}")
            print(f"[Debug {self.name}] BadRequest Detail: {error_desc}")
            error_json_str = json.dumps({"ok": False, "error_code": error_code, "description": error_desc})
            return error_code, error_json_str, len(error_json_str.encode('utf-8')), False
            
        except TimedOut as e:
            error_desc = e.message
            error_code = 504 # Assume 504
            print(f"{self.name} sender TimedOut: {error_desc}")
            print(f"[Debug {self.name}] TimedOut Detail: {error_desc}")
            error_json_str = json.dumps({"ok": False, "error_code": error_code, "description": error_desc})
            return error_code, error_json_str, len(error_json_str.encode('utf-8')), False
            
        except NetworkError as e: # More general network issue
            error_desc = e.message
            error_code = 503 # Assume 503
            print(f"{self.name} sender NetworkError: {error_desc}")
            print(f"[Debug {self.name}] NetworkError Detail: {error_desc}")
            error_json_str = json.dumps({"ok": False, "error_code": error_code, "description": error_desc})
            return error_code, error_json_str, len(error_json_str.encode('utf-8')), False
            
        except TelegramError as e: # Catch other Telegram-specific errors
            error_desc = e.message
            error_code = 500 # Assume generic 500
            print(f"{self.name} sender TelegramError: {error_desc}")
            print(f"[Debug {self.name}] TelegramError Detail: Type={type(e).__name__}, Error={error_desc}")
            error_json_str = json.dumps({"ok": False, "error_code": error_code, "description": error_desc})
            return error_code, error_json_str, len(error_json_str.encode('utf-8')), False
            
        except Exception as e:
            error_desc = str(e)
            error_code = 500 # Assume generic 500
            print(f"{self.name} sender general error: {e}")
            print(f"[Debug {self.name}] General Error Detail: Type={type(e).__name__}, Error={error_desc}")
            error_json_str = json.dumps({"ok": False, "error_code": error_code, "description": error_desc})
            return error_code, error_json_str, len(error_json_str.encode('utf-8')), False

    def send_message_sync(self, db_conn, text_payload, message_params):
        raise NotImplementedError(f"{self.name} is implemented as asynchronous only (PTB v20+).")

    def get_sender_type(self):
        return "async"

    def get_library_version(self):
        try:
            from telegram import __version__ as ptb_version
            return ptb_version
        except ImportError:
            return "python-telegram-bot (version not found)" 