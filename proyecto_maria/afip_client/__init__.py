"""AFIP integration package.

This module provides helpers to interact with AFIP web services.  At the
moment the implementation only contains skeletons so the rest of the
application can be developed and tested without credentials.  Once we obtain
the certificates and service URLs, we can plug the real logic here without
touching the rest of the codebase.

Submodules:
    config: Settings loader (environment variables, paths).
    wsaa:   Stub client for WSAA authentication workflow.
    services: Placeholders for individual SOAP services (e.g. wgestabref).
"""

from .config import AFIPSettings
from .wsaa import WSAAClient

__all__ = ["AFIPSettings", "WSAAClient"]


