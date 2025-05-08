from telebot.async_telebot import AsyncTeleBot
from telebot.apihelper import ApiTelegramException
from telebot.types import Message # For type hinting
import json
import importlib.metadata # Import the metadata module

from .base_sender import BaseSender # Removed PerformanceStats

class PyTelegramBotAPISender(BaseSender):
    name = "pytelegrambotapi"
    _bot: AsyncTeleBot = None

    async def initialize_session(self):
        """Initializes the AsyncTeleBot object."""
        if not self.config.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in config for PyTelegramBotAPISender.")
        
        # AsyncTeleBot manages its own aiohttp.ClientSession internally.
        # We can pass custom loop or proxy settings if needed, but defaults are fine for benchmark.
        self._bot = AsyncTeleBot(token=self.config.TELEGRAM_BOT_TOKEN)
        
        # The "session" for BaseSender is the AsyncTeleBot instance.
        # No explicit initialize() call seems to be required before first use, 
        # session is created on demand or with first call.
        return self._bot

    async def close_session(self, session: AsyncTeleBot):
        """Closes the AsyncTeleBot's internal aiohttp session."""
        # 'session' is the self._bot instance.
        if session: # Which is self._bot
            await session.close_session() # This is the method to close its underlying client session
        self._bot = None

    async def send_message_async(self, 
                                 session: AsyncTeleBot, # Add session parameter
                                 db_conn, # Ignored
                                 text_payload: str, 
                                 message_params: dict # Ignored
                                 ) -> tuple[int, str, int, bool]: # Corrected return signature
        """Sends a message using the initialized AsyncTeleBot."""
        # session argument is present to match BaseSender, but self._bot is used internally.
        if not self._bot:
            raise RuntimeError("AsyncTeleBot not initialized. Call initialize_session first.")

        api_payload_text = text_payload # Use DB message directly
        
        try:
            sent_message_obj: Message = await self._bot.send_message(chat_id=self.chat_id, text=api_payload_text)
            
            status_code = 200 # Inferred success
            response_dict = {}
            if sent_message_obj:
                response_size = len(str(sent_message_obj).encode('utf-8')) # Fallback size
                # Try to get a string representation for response_text
                if hasattr(sent_message_obj, 'json_string'):
                    response_text = sent_message_obj.json_string
                    response_size = len(response_text.encode('utf-8'))
                elif hasattr(sent_message_obj, 'to_dict'):
                    try:
                        response_text = json.dumps(sent_message_obj.to_dict())
                        response_size = len(response_text.encode('utf-8'))
                    except Exception as e_dict:
                        print(f"[Debug {self.name}] Error using to_dict(): {e_dict}")
                        response_text = str(sent_message_obj)
                elif hasattr(sent_message_obj, 'json'): # Typically a property, not a method
                    try:
                        response_text = json.dumps(sent_message_obj.json) # If .json is already a dict/list
                        response_size = len(response_text.encode('utf-8'))
                    except TypeError:
                        try:
                            response_text = sent_message_obj.json # If .json is a string
                            response_size = len(response_text.encode('utf-8'))
                        except Exception as e_json_prop:
                            print(f"[Debug {self.name}] Error using .json property: {e_json_prop}")
                            response_text = str(sent_message_obj)
                    except Exception as e_json:
                        print(f"[Debug {self.name}] Error using .json: {e_json}")
                        response_text = str(sent_message_obj)
                elif hasattr(sent_message_obj, 'text'): # For simple text responses
                    response_text = str(sent_message_obj.text)
                    response_size = len(response_text.encode('utf-8'))
                else:
                    response_text = str(sent_message_obj)
            success = True # Assuming success if no exception before this
            
            return status_code, response_text, response_size, success

        except ApiTelegramException as e:
            # Specific logging for pyTelegramBotAPI errors
            status_code = e.error_code if isinstance(e.error_code, int) else 500
            error_desc = e.description
            print(f"{self.name} sender ApiTelegramException: {status_code} - {error_desc}")
            
            response_body_str = ""
            if e.result and isinstance(e.result, (str, bytes)):
                response_body_str = e.result.decode('utf-8') if isinstance(e.result, bytes) else str(e.result)
                print(f"[Debug {self.name}] ApiTelegramException Response Body: {response_body_str[:500]}") # Log response body
            else:
                print(f"[Debug {self.name}] ApiTelegramException: No response body available. Description: {error_desc}")
                response_body_str = json.dumps({"ok": False, "error_code": status_code, "description": error_desc})
            
            response_size = len(response_body_str.encode('utf-8'))
            return status_code, response_body_str, response_size, False
            
        except Exception as e:
            # Specific logging for general errors
            error_desc = str(e)
            error_code = 500 # Assume generic 500
            print(f"{self.name} sender general error: {e}")
            print(f"[Debug {self.name}] General Error Detail: Type={type(e).__name__}, Error={error_desc}")
            error_response_str = json.dumps({"ok":False, "description": error_desc})
            return error_code, error_response_str, len(error_response_str.encode('utf-8')), False

    def send_message_sync(self, db_conn, text_payload, message_params):
        raise NotImplementedError(f"{self.name} is implemented as asynchronous only.")

    def get_sender_type(self):
        return "async"

    def get_library_version(self):
        try:
            # Use importlib.metadata to get the installed version
            return importlib.metadata.version('pyTelegramBotAPI')
        except importlib.metadata.PackageNotFoundError:
            return "pyTelegramBotAPI (version not found)"
        except ImportError:
            # Fallback for older environments if importlib.metadata itself is missing?
            # Unlikely in modern Python, but safe to include.
            try:
                # Try pkg_resources as a fallback
                import pkg_resources
                return pkg_resources.get_distribution("pyTelegramBotAPI").version
            except Exception:
                return "pyTelegramBotAPI (version not found)" 