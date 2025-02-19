import logging
import os

from .config import config

_LOGGER = logging.getLogger(__name__)


def get_llm_params(platform: str = "vertexai"):
    conf = dir(config)
    params = {
        c.split(platform.upper() + "_")[-1].lower(): getattr(config, c)
        for c in conf
        if platform in c.lower()
    }
    return params
