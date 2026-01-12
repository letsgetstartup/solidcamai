import os
import requests
from typing import Optional, Tuple
from simco_agent.config import settings

class DeviceIdentity:
    """Handles X.509 device identity for mTLS communication."""

    def __init__(self):
        self.cert_path = settings.DEVICE_CERT_PATH
        self.key_path = settings.DEVICE_KEY_PATH
        self.ca_path = settings.CA_CERT_PATH

    @property
    def is_mtls_enabled(self) -> bool:
        return bool(self.cert_path and self.key_path)

    def get_mtls_params(self) -> dict:
        """Returns parameters for requests.get/post for mTLS."""
        params = {}
        if self.is_mtls_enabled:
            params["cert"] = (self.cert_path, self.key_path)
        if self.ca_path:
            params["verify"] = self.ca_path
        return params

    def secure_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Performs a secure HTTP request using mTLS identity."""
        mtls_params = self.get_mtls_params()
        # Merge kwargs with mtls_params, kwargs takes precedence
        final_kwargs = {**mtls_params, **kwargs}
        return requests.request(method, url, **final_kwargs)
