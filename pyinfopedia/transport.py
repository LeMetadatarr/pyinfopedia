from __future__ import annotations

from typing import Any, Dict, Optional

from unblock_requests import CloudflareSession

ENV_PREFIX = "PYINFOPEDIA"

_USER_AGENT = (
    "pyinfopedia/0.0.1 (TigreGotico Portuguese dictionary client; "
    "https://github.com/TigreGotico/pyinfopedia)"
)

_VALID_MODES = {"requests", "curl_cffi", "wayback", "flaresolverr"}


class Transport:
    def __init__(self, *, mode: Optional[str] = None,
                 flaresolverr_url: Optional[str] = None,
                 flaresolverr_timeout_ms: Optional[int] = None,
                 wayback_fallback: Optional[bool] = None) -> None:
        if mode is not None and mode.lower() not in _VALID_MODES:
            raise ValueError(
                f"mode must be one of {sorted(_VALID_MODES)} or None, got {mode!r}"
            )
        self.mode = mode.lower() if mode else None
        self.flaresolverr_url = flaresolverr_url
        self.flaresolverr_timeout_ms = flaresolverr_timeout_ms
        self.wayback_fallback = wayback_fallback
        self._session: Optional[CloudflareSession] = None

    @property
    def session(self) -> CloudflareSession:
        if self._session is None:
            self._session = CloudflareSession(
                mode=self.mode,
                flaresolverr_url=self.flaresolverr_url,
                flaresolverr_timeout_ms=self.flaresolverr_timeout_ms,
                wayback_fallback=self.wayback_fallback,
                env_prefix=ENV_PREFIX,
            )
            self._session.headers.update({"User-Agent": _USER_AGENT})
        return self._session

    def _resolved_mode(self) -> str:
        return self.session._resolved_mode()

    def get_text(self, url: str, *, params: Optional[Dict[str, Any]] = None,
                 timeout: int = 30) -> str:
        r = self.session.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.text

    def get_json(self, url: str, *, params: Optional[Dict[str, Any]] = None,
                 timeout: int = 30) -> Dict[str, Any]:
        r = self.session.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()


_DEFAULT_TRANSPORT: Optional[Transport] = None


def default_transport() -> Transport:
    global _DEFAULT_TRANSPORT
    if _DEFAULT_TRANSPORT is None:
        _DEFAULT_TRANSPORT = Transport()
    return _DEFAULT_TRANSPORT
