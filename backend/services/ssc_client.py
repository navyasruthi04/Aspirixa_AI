"""
Polite HTTP client for ssc.gov.in.

Rules it follows:
  * talks ONLY to ssc.gov.in over https (also checks every redirect)
  * waits between requests (default 2 seconds)
  * retries network errors / 5xx / 429 with growing waits
  * obeys robots.txt
  * if the site answers 401/403 it STOPS. It never tries to get around a block.
"""
import time
import urllib.robotparser
from urllib.parse import urlparse, urljoin

import requests

ALLOWED_HOST = "ssc.gov.in"
BASE_URL = f"https://{ALLOWED_HOST}"
USER_AGENT = "AspirixaAI-NoticeSync/1.0 (student project; reads public notices only)"

NOTICE_API = f"{BASE_URL}/api/general-website/portal/notice-boards"
ATTACHMENT_BASE = f"{BASE_URL}/api/attachment/uploads/masterData/NoticeBoards/"

MAX_PDF_BYTES = 25 * 1024 * 1024


class SyncError(Exception):
    """Temporary problem (network, server error). Safe to try again later."""


class BlockedError(SyncError):
    """The site refused us (401/403) or robots.txt forbids it. Do not retry."""


def is_allowed_url(url):
    try:
        p = urlparse(url)
    except Exception:
        return False
    return p.scheme == "https" and p.hostname == ALLOWED_HOST


class SSCClient:
    def __init__(self, session=None, delay=2.0, retries=3, backoff=2.0,
                 timeout=20, base_url=BASE_URL, check_robots=True):
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept": "*/*"})
        self.delay = delay
        self.retries = retries
        self.backoff = backoff
        self.timeout = timeout
        self.base_url = base_url
        self.check_robots = check_robots
        self._last_request = 0.0
        self._robots = None

    # -- internals ------------------------------------------------------
    def _wait_turn(self):
        gap = time.monotonic() - self._last_request
        if gap < self.delay:
            time.sleep(self.delay - gap)
        self._last_request = time.monotonic()

    def _check_url(self, url):
        # Tests point base_url at a local fake server; real use is ssc.gov.in only.
        if self.base_url == BASE_URL and not is_allowed_url(url):
            raise BlockedError(f"Refusing to contact {url!r}: only {ALLOWED_HOST} is allowed.")

    def _robots_allows(self, url):
        if not self.check_robots:
            return True
        if self._robots is None:
            rp = urllib.robotparser.RobotFileParser()
            resp = self._get_raw(urljoin(self.base_url, "/robots.txt"), skip_robots=True)
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
            elif 400 <= resp.status_code < 500:
                rp.parse([])               # no robots.txt means no restriction
            else:
                raise SyncError(f"robots.txt returned HTTP {resp.status_code}")
            self._robots = rp
        return self._robots.can_fetch(USER_AGENT, url)

    def _get_raw(self, url, skip_robots=False, stream=False, params=None):
        self._check_url(url)
        last_error = None

        for attempt in range(self.retries):
            if attempt:
                time.sleep(self.backoff * (2 ** (attempt - 1)))

            self._wait_turn()
            try:
                resp = self.session.get(
                    url, params=params, timeout=self.timeout,
                    allow_redirects=False, stream=stream,
                )
            except requests.RequestException as exc:
                last_error = f"network error: {exc.__class__.__name__}"
                continue

            # Follow redirects by hand so we can check each destination
            hops = 0
            while resp.is_redirect and hops < 3:
                target = urljoin(url, resp.headers.get("Location", ""))
                self._check_url(target)
                self._wait_turn()
                try:
                    resp = self.session.get(target, timeout=self.timeout,
                                            allow_redirects=False, stream=stream)
                except requests.RequestException as exc:
                    last_error = f"network error: {exc.__class__.__name__}"
                    resp = None
                    break
                hops += 1
            if resp is None:
                continue

            if resp.status_code in (401, 403):
                raise BlockedError(f"SSC refused access (HTTP {resp.status_code}). Not retrying.")
            if resp.status_code == 429 or resp.status_code >= 500:
                last_error = f"HTTP {resp.status_code}"
                continue
            return resp

        raise SyncError(f"Gave up after {self.retries} attempts ({last_error}).")

    # -- public ---------------------------------------------------------
    def get_json(self, url, params=None):
        if not self._robots_allows(url):
            raise BlockedError("robots.txt does not allow this address.")
        resp = self._get_raw(url, params=params)
        if resp.status_code != 200:
            raise SyncError(f"HTTP {resp.status_code} from {url}")
        try:
            return resp.json()
        except ValueError:
            raise SyncError("The notice list was not valid JSON (the site may have changed).")

    def get_pdf(self, url):
        if not self._robots_allows(url):
            raise BlockedError("robots.txt does not allow this address.")
        resp = self._get_raw(url, stream=True)
        if resp.status_code != 200:
            raise SyncError(f"HTTP {resp.status_code} for the PDF")
        data = b""
        for chunk in resp.iter_content(65536):
            data += chunk
            if len(data) > MAX_PDF_BYTES:
                raise SyncError("PDF is larger than 25 MB; skipped.")
        if not data.startswith(b"%PDF"):
            raise SyncError("The downloaded file is not a PDF.")
        return data
