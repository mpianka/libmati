import os
import yaml
from libmati.utils import logging
from typing import OrderedDict, Any
import re

log = logging.get_logger(__name__)


class YamlConfig:
    def __init__(self, path: str = None):
        self.path = path
        self.config: dict = dict()

    @property
    def config_path(self):
        return self.path or os.path.join(os.getcwd(), "libmati.yaml")

    def load(self):
        if os.path.exists(self.config_path):
            log.info(f"Config file {self.config_path} exists, trying to load")
        else:
            log.error(f"Config file {self.config_path} doesn't exist. Exiting...")
            raise FileNotFoundError()

        with open(self.config_path) as f:
            self.config = yaml.full_load(f)
            log.info(f"Config file {self.config_path} loaded properly")

        return self.config

    def get(self, attr_path: str, default: Any = None):
        return sget(self.config, attr_path, default)


def sget(obj: dict, attr_path: str, default: Any = None):
    attr_path: list = attr_path.split(".")
    result = obj

    for attr in attr_path:
        try:
            if isinstance(result, (dict, OrderedDict)):
                result = result[attr]
            elif isinstance(result, (list, tuple)) and re.match(r"^-?\d+$", attr):
                result = result[int(attr)]
            else:
                result = getattr(result, attr)
        except (AttributeError, KeyError, IndexError):
            return default

    return result
