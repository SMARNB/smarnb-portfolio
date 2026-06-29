#!/usr/bin/env python3
"""Keep the Render free-tier site warm so first visits are instant.

Render's free web service sleeps after ~15 minutes with no traffic; the next
request then pays a 1-3 minute cold start (and a fresh Neon DB connection). This
script *is* the visitor: it pings an endpoint that wakes both the app and the
database on a schedule, so a real visitor never hits a sleeping server.

Why /api/services and not /api/health: /api/services runs a real DB query, so it
warms the Neon Postgres connection too — /api/health would only wake the web app.

Standard library only (no pip install). Configurable, with timeout, retries and
clear logging.

Usage:
    python keepalive.py                         # single ping (good for cron / CI)
    python keepalive.py https://example.com     # override the base URL
    python keepalive.py --loop                  # run forever, ping every interval
    python keepalive.py --loop --interval 600   # ...every 600s (10 min)

Environment variables (CLI flags win over these):
    KEEPALIVE_URL       Full URL to ping     (default: <base>/api/services)
    KEEPALIVE_BASE      Base site URL        (default: https://smarnb.onrender.com)
    KEEPALIVE_TIMEOUT   Per-request seconds  (default: 60)
    KEEPALIVE_RETRIES   Attempts per ping    (default: 3)
    KEEPALIVE_INTERVAL  Seconds between pings in --loop (default: 600 = 10 min)

Exit code: 0 if the ping ultimately succeeded, 1 otherwise (so CI/cron can alert).
"""
import argparse
import logging
import os
import sys
import time
import urllib.error
import urllib.request

DEFAULT_BASE = "https://smarnb.onrender.com"


def _env(name, default):
    val = os.environ.get(name)
    return val if val not in (None, "") else default


def resolve_url(cli_url):
    if cli_url:
        return cli_url
    explicit = _env("KEEPALIVE_URL", "")
    if explicit:
        return explicit
    base = _env("KEEPALIVE_BASE", DEFAULT_BASE).rstrip("/")
    # An endpoint that touches the DB, so we warm app + Neon in one request.
    return base + "/api/services"


def ping_once(url, timeout, retries, log):
    """Ping `url`, retrying with exponential backoff. Return True on success.

    A cold start can take a while, so the first attempt may legitimately be slow;
    that's exactly the request we're paying so a real visitor doesn't have to."""
    last_err = None
    for attempt in range(1, retries + 1):
        started = time.time()
        try:
            req = urllib.request.Request(
                url, method="GET",
                headers={"User-Agent": "smarnb-keepalive/1.0 (+uptime ping)"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                elapsed = time.time() - started
                # Drain a little so the connection completes cleanly.
                resp.read(2048)
                log.info("OK %s -> HTTP %s in %.1fs (attempt %d/%d)",
                         url, resp.status, elapsed, attempt, retries)
                if elapsed > 20:
                    log.info("  (slow response — server was likely asleep; it's warm now)")
                return True
        except urllib.error.HTTPError as e:
            # The server answered (so it's awake) even if the status isn't 2xx.
            elapsed = time.time() - started
            log.warning("HTTP %s from %s in %.1fs (attempt %d/%d)",
                        e.code, url, elapsed, attempt, retries)
            if 200 <= e.code < 500:
                # 4xx still means the app is awake — treat as a successful wake-up.
                return True
            last_err = e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            elapsed = time.time() - started
            last_err = e
            log.warning("ping failed in %.1fs (attempt %d/%d): %s",
                        elapsed, attempt, retries, e)
        if attempt < retries:
            backoff = min(30, 2 ** attempt)
            log.info("retrying in %ds...", backoff)
            time.sleep(backoff)
    log.error("all %d attempts failed for %s: %s", retries, url, last_err)
    return False


def main(argv=None):
    parser = argparse.ArgumentParser(description="Keep the Render site warm.")
    parser.add_argument("url", nargs="?", help="URL to ping (default: <base>/api/services)")
    parser.add_argument("--loop", action="store_true",
                        help="run continuously instead of a single ping")
    parser.add_argument("--interval", type=int,
                        default=int(_env("KEEPALIVE_INTERVAL", "600")),
                        help="seconds between pings in --loop mode (default 600)")
    parser.add_argument("--timeout", type=int,
                        default=int(_env("KEEPALIVE_TIMEOUT", "60")),
                        help="per-request timeout in seconds (default 60)")
    parser.add_argument("--retries", type=int,
                        default=int(_env("KEEPALIVE_RETRIES", "3")),
                        help="attempts per ping (default 3)")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    log = logging.getLogger("keepalive")

    url = resolve_url(args.url)

    if not args.loop:
        ok = ping_once(url, args.timeout, args.retries, log)
        return 0 if ok else 1

    log.info("keep-alive loop started: pinging %s every %ds", url, args.interval)
    try:
        while True:
            ping_once(url, args.timeout, args.retries, log)
            time.sleep(max(60, args.interval))
    except KeyboardInterrupt:
        log.info("stopped.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
