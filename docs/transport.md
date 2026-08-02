# Transport

All HTTP goes through `Transport`, a thin wrapper over
`unblock_requests.CloudflareSession`. Infopédia sits behind Cloudflare, so the
transport chooses how requests are made and how the challenge is handled.

```python
from pyinfopedia import Transport, get_word

t = Transport(mode="curl_cffi")
entry = get_word("casa", transport=t)
```

## Modes

| mode | how it fetches |
|---|---|
| `requests` | plain `requests` session |
| `curl_cffi` | browser-impersonating TLS via `curl_cffi` (install `pyinfopedia[stealth]`) |
| `flaresolverr` | delegates to a running [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) instance |
| `wayback` | reads the page from the Wayback Machine |

`mode=None` lets `unblock_requests` pick its default strategy.

## Constructor

```python
Transport(
    *,
    mode: str | None = None,
    flaresolverr_url: str | None = None,
    flaresolverr_timeout_ms: int | None = None,
    wayback_fallback: bool | None = None,
)
```

For `flaresolverr`, point at the instance:

```python
t = Transport(mode="flaresolverr", flaresolverr_url="http://host:8191")
```

## Default transport

`default_transport()` returns the transport used when a lookup is called without
an explicit `transport=`. The `Infopedia` client builds and reuses one transport
for all its calls.

## Choosing a mode

- `curl_cffi` is usually enough to pass the Cloudflare check from a normal host.
- `flaresolverr` is the most robust when the check is strict; it needs a separate
  FlareSolverr service.
- `wayback` avoids the live site entirely but only sees archived pages.
