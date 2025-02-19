import logging

from requests import RequestException

from core.config import config as c
from core.exceptions import FAQError
from datamodel.faq import FAQ, FAQPayload
from services.base import BaseService

_LOGGER = logging.getLogger(__name__)


class FAQService(BaseService):
    """FAQ Service."""
    def __init__(self, base_url: str, port: int):
        super().__init__(base_url, port)

    def generate(self, period: str = "") -> FAQ:
        """Generate FAQ for given period.

        Args:
            period (str, optional): Period to generate. Defaults to "".
                If "", will get the latest generated FAQ. Should be in format
                "YYYY-MM-DD".

        Returns:
            FAQ: Generated FAQ.
        """
        payload = FAQPayload(date=period)
        try:
            response = self.session.get(
                f"{self.base_url}:{self.port}"
                f"{c.CHATBOT_ENDPOINT}{c.FAQ_ENDPOINT}",
                params=payload.model_dump()
            )
            if response.status_code != 200:
                _LOGGER.exception("Got status code %s", response.status_code)
                response.raise_for_status()
            _LOGGER.info("Got %d FAQs", response.json()["total_item"])
        except RequestException as exc:
            raise FAQError("Error when generating FAQ") from exc

        return FAQ.model_validate(response.json())
