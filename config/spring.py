"""Module for retrieve application's config from Spring Cloud Config."""
import logging
import os
from typing import Any, Callable, Dict, KeysView

import attr
import requests
from glom import glom

from config.core import singleton
from config.exceptions import RequestFailedException

logging.getLogger(__name__).addHandler(logging.NullHandler())


@attr.s(slots=True)
class ConfigClient:
    """Spring Cloud Config Client."""

    address = attr.ib(
        type=str, default=os.getenv("CONFIGSERVER_ADDRESS", "http://localhost:8888")
    )
    branch = attr.ib(type=str, default=os.getenv("BRANCH", "master"))
    app_name = attr.ib(
        type=str,
        default=os.getenv("APP_NAME", ""),
        validator=attr.validators.instance_of(str),
    )
    profile = attr.ib(type=str, default=os.getenv("PROFILE", "development"))
    url = attr.ib(type=str, default="{address}/{branch}/{app_name}-{profile}")
    fail_fast = attr.ib(
        type=bool, default=True, validator=attr.validators.instance_of(bool)
    )
    _config = attr.ib(
        type=dict,
        default={},
        init=False,
        validator=attr.validators.instance_of(dict),
        repr=False,
    )

    def __attrs_post_init__(self) -> None:
        """Format ConfigClient URL."""
        self.url = self.url.format(
            address=self.address,
            branch=self.branch,
            app_name=self.app_name,
            profile=self.profile,
        )

    def get_config(self, headers: dict = {}) -> None:
        response = self._request_config(headers)
        if response.ok:
            self._config = response.json()
        else:
            raise RequestFailedException(
                "Failed to request the configurations. "
                f"HTTP Response code: {response.status_code}."
            )

    def _request_config(self, headers: dict) -> requests.Response:
        try:
            response = requests.get(self.url, headers=headers)
        except Exception:
            logging.error("Failed to establish connection with ConfigServer.")
            if self.fail_fast:
                logging.info("fail_fast enabled (True). Terminating process.")
                raise SystemExit(1)
            raise ConnectionError("fail_fast disabled (False).")
        return response

    @property
    def config(self) -> Dict:
        """Getter from configurations retrieved from ConfigClient."""
        return self._config

    def get_attribute(self, value: str) -> Any:
        """
        Get attribute from configuration.

        :value value: -- The filter to query on dict.
        :return: The value matches or ''
        """
        return glom(self._config, value, default="")

    def get_keys(self) -> KeysView:
        """List all keys from configuration retrieved."""
        return self._config.keys()


@singleton
def create_config_client(**kwargs) -> ConfigClient:
    """
    Create ConfigClient singleton instance.

    :param address:
    :param app_name:
    :param branch:
    :param fail_fast:
    :param profile:
    :param url:
    :return: ConfigClient instance.
    """
    obj = ConfigClient(**kwargs)
    obj.get_config()
    return obj


def config_client(*args, **kwargs) -> Callable[[Dict[str, str]], ConfigClient]:
    """ConfigClient decorator.

    Usage:

    @config_client(app_name='test')
    def get_config(config):
        db_user = config.get_attribute('database.user')

    :raises: ConnectionError: If fail_fast enabled.
    :return: ConfigClient instance.
    """
    logging.debug(f"args: {args}")
    logging.debug(f"kwargs: {kwargs}")

    def wrap_function(function):
        logging.debug(f"caller: {function}")

        def enable_config():
            obj = ConfigClient(*args, **kwargs)
            obj.get_config()
            return function(obj)

        return enable_config

    return wrap_function
