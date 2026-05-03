"""Configuration helpers for AFIP integrations.

This file centralises all environment-driven settings so the rest of the
codebase can simply depend on `AFIPSettings`.  For now we expose only the
fields required to bootstrap WSAA.  All values are optional to avoid
breaking local development workflows; when credentials are missing we skip
real calls and fall back to stubs.

Usage:
    from afip_client.config import AFIPSettings
    settings = AFIPSettings.from_env()
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass
class AFIPSettings:
    """Container for AFIP configuration.

    Attributes:
        service: Name of the AFIP service to request via WSAA (e.g. "wsctg").
        cert_path: Path to the X.509 certificate (.crt/.pem).
        key_path: Path to the private key associated with the certificate.
        wsaa_url: URL of the WSAA login endpoint (homologación o producción).
    """

    service: str | None = None
    cert_path: Path | None = None
    key_path: Path | None = None
    wsaa_url: str | None = None

    @classmethod
    def from_env(cls) -> "AFIPSettings":
        """Create settings reading from environment variables.

        Environment variables used:
            AFIP_SERVICE
            AFIP_CERT_PATH
            AFIP_KEY_PATH
            AFIP_WSAA_URL
        """

        cert_env = os.getenv("AFIP_CERT_PATH")
        key_env = os.getenv("AFIP_KEY_PATH")

        cert_path = Path(cert_env).expanduser() if cert_env else None
        key_path = Path(key_env).expanduser() if key_env else None

        return cls(
            service=os.getenv("AFIP_SERVICE"),
            cert_path=cert_path if cert_path and cert_path.exists() else None,
            key_path=key_path if key_path and key_path.exists() else None,
            wsaa_url=os.getenv(
                "AFIP_WSAA_URL",
                "https://wsaahomo.afip.gov.ar/ws/services/LoginCms",  # default homologación
            ),
        )

    def is_configured(self) -> bool:
        """Return True when we have enough data to perform real calls."""

        return bool(self.service and self.cert_path and self.key_path)


