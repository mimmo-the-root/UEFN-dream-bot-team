"""Router v2 error handling (T-033, pure, no network): error classes, retry-after, backoff, fallback chain.
Every function takes its clock / rng as a parameter so tests are deterministic."""
import random
import time

RETRY_AFTER_MIN, RETRY_AFTER_MAX = 1.0, 60.0
BACKOFF_MIN, BACKOFF_MAX = 1.0, 30.0


def classify_status(status):
    """HTTP status (0 = network failure/timeout) -> 'rate_limit' | 'timeout_conflict' | 'server' | 'network' | 'other'."""
    try:
        status = int(status or 0)
    except (TypeError, ValueError):
        return "other"
    if status == 0:
        return "network"
    if status == 429:
        return "rate_limit"
    if status in (408, 409):
        return "timeout_conflict"
    if 500 <= status <= 599:
        return "server"
    return "other"


def is_retryable(error_class):
    return error_class in ("rate_limit", "timeout_conflict", "server", "network")


def parse_retry_after(value, now=None):
    """Retry-After header (seconds, or an HTTP date) -> seconds clamped to 1-60, or None when absent/unreadable."""
    if value is None or str(value).strip() == "":
        return None
    v = str(value).strip()
    try:
        secs = float(v)
    except ValueError:
        try:
            from email.utils import parsedate_to_datetime
            secs = parsedate_to_datetime(v).timestamp() - (time.time() if now is None else now)
        except Exception:
            return None
    if secs != secs:  # NaN
        return None
    return max(RETRY_AFTER_MIN, min(RETRY_AFTER_MAX, secs))


def backoff_seconds(attempt, rng=None, base=1.0):
    """Exponential backoff with full jitter in the upper half, clamped to 1-30 s. attempt starts at 0."""
    rng = rng or random
    raw = min(BACKOFF_MAX, base * (2 ** max(0, int(attempt))))
    return max(BACKOFF_MIN, min(BACKOFF_MAX, raw * (0.5 + 0.5 * rng.random())))


def pause_for(status, retry_after_header=None, attempt=0, rng=None, now=None):
    """Seconds to leave a provider alone after a failure (0 when the failure is not retryable)."""
    cls = classify_status(status)
    if not is_retryable(cls):
        return 0.0
    ra = parse_retry_after(retry_after_header, now)
    if cls == "rate_limit" and ra is not None:
        return ra
    return backoff_seconds(attempt, rng)


def mark_failure(skip, provider, status, retry_after_header=None, attempt=0, rng=None, clock=time.time):
    """Record in `skip` (dict provider -> resume time) that the provider is resting; returns the pause (0 = not recorded)."""
    p = pause_for(status, retry_after_header, attempt, rng, clock())
    if p:
        skip[provider] = clock() + p
    return p


def chain_after(chain, skip, clock=time.time):
    """The fallback chain without the providers still inside their retry window, original order kept."""
    now = clock()
    return [n for n in chain if skip.get(n, 0) <= now]
