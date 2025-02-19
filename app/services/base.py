"""Base service module."""
from dataclasses import dataclass
from http import HTTPStatus

import requests
from requests import RequestException
from requests.adapters import HTTPAdapter
from urllib3 import Retry


@dataclass
class BaseService:
    base_url: str
    port: int

    def __post_init__(self):
        if "http" not in self.base_url:
            self.base_url = "http://" + self.base_url

    @property
    def session(self):
        """
        Returns:
            requests.Session
        """
        if not hasattr(self, "_session"):
            session = requests.Session()
            retries = Retry(
                total=5,
                backoff_factor=0.1,
                status_forcelist=[
                    HTTPStatus.REQUEST_TIMEOUT,
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    HTTPStatus.BAD_GATEWAY,
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    HTTPStatus.GATEWAY_TIMEOUT,
                ],
            )
            adapter = HTTPAdapter(
                max_retries=retries,
                pool_connections=5,
                pool_maxsize=5,
            )
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            setattr(self, "_session", session)
        return getattr(self, "_session")
