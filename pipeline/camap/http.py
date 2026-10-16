"""Minimal polite HTTP JSON client (stdlib only)."""
import json
import time
import urllib.error
import urllib.request

USER_AGENT = "IDT_ca_map/0.1 (literature curation; contact via github.com/Nurtal/IDT_ca_map)"
_last_call = [0.0]


def get_json(url, min_interval=0.35, retries=3):
    return json.loads(get_text(url, min_interval, retries))


def get_text(url, min_interval=0.35, retries=3):
    for attempt in range(retries):
        wait = min_interval - (time.monotonic() - _last_call[0])
        if wait > 0:
            time.sleep(wait)
        _last_call[0] = time.monotonic()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError):
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt * 2)
    raise RuntimeError("unreachable")
