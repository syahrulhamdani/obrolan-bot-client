from collections.abc import AsyncGenerator
import json
import logging
import sys

import aiohttp
from requests import RequestException

from core.config import config as c
from core.exceptions import ChatError
from datamodel.chat import ChatQuery
from datamodel.feedback import Feedback
from datamodel.response import ResponseWithSources
from services.base import BaseService

_LOGGER = logging.getLogger(__name__)


class ChatbotService(BaseService):
    """Chatbot service."""
    def __init__(self, base_url: str, port: int):
        super().__init__(base_url, port)

    def chat(self, query: ChatQuery) -> ResponseWithSources:
        try:
            response = self.session.post(
                f"{self.base_url}:{self.port}{c.CHATBOT_ENDPOINT}/chat",
                json=query.model_dump(),
            )
            if response.status_code != 200:
                _LOGGER.exception("Got status code %s", response.status_code)
                response.raise_for_status()
        except RequestException as exc:
            raise ChatError("Error when processing chat") from exc

        return ResponseWithSources(**response.json())

    def reset_session(self, session_id: str):
        try:
            response = self.session.post(
                f"{self.base_url}:{self.port}{c.CHATBOT_ENDPOINT}/reset_session",
                params={"session_id": session_id},
            )
            if response.status_code != 200:
                _LOGGER.exception("Got status code %s", response.status_code)
                response.raise_for_status()
        except RequestException as exc:
            raise ChatError("Error when resetting session") from exc

    def send_feedback(self, feedback: Feedback):
        try:
            response = self.session.post(
                f"{self.base_url}:{self.port}{c.CHATBOT_ENDPOINT}"
                "/feedback/send",
                json=feedback.model_dump(),
            )
            if response.status_code != 200:
                _LOGGER.exception("Got status code %s", response.status_code)
                response.raise_for_status()
        except RequestException as exc:
            raise ChatError("Error when sending feedback") from exc

        return response.json()


    async def stream_gemini(
        self,
        query: ChatQuery
    ) -> AsyncGenerator[str | tuple[str, str], None]:
        """
        Calls the given Gemini model with the given text content,
        streaming output as an async generator.
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}:{self.port}{c.CHATBOT_ENDPOINT}/chat/stream",
                headers={
                    "content-type": "application/json",
                    "Accept": "text/event-stream"
                },
                json=query.model_dump(),
            ) as response:
                if response.status != 200:
                    yield f"Error: Status {response.status}"
                    return

                async for chunk in self.stream_response_chunks(response):
                    yield chunk

    async def stream_response_chunks(self, response):
        previous_response = ""
        first_chunk = True

        try:
            async for chunk in response.content:
                decoded_chunk = chunk.decode()
                try:
                    # Parse the JSON from the response
                    data = json.loads(decoded_chunk)
                    # Get the current response
                    current_response = data.get('response', '')
                    if not current_response:
                        continue

                    # Handle the response differently for first chunk
                    if first_chunk:
                        if current_response.strip():
                            yield current_response  # Remove strip() to keep all characters
                        first_chunk = False
                        previous_response = current_response
                    # For subsequent chunks, check if it's a completely new response
                    elif current_response != previous_response:

                        # If current response contains the complete text (including first part)
                        if len(current_response) > 0:
                            yield current_response

                        previous_response = current_response

                    # Check if the response is complete
                    if data.get('is_complete', False):
                        _LOGGER.info("Response is complete")
                        yield data.get('session_id'), data.get('message_id')
                        break

                except json.JSONDecodeError as e:
                    _LOGGER.exception("Failed to parse chunk JSON: %s", e)
                    raise e

        except Exception as e:
            _LOGGER.info("Exception occurred: %s", e)
            raise e
