"""
Turns SSC notice-board JSON and notice PDFs into clean, validated values.

The notice-board JSON field names (id, headline, examId, redirectUrl, startDate,
endDate, createdAt) come from the attributes list in the request URL you found.
The exact wrapper around the list is not confirmed yet, so extract_items()
accepts several shapes. Run probe_ssc.py to see the real response.
"""
import re
from datetime import date, datetime
from urllib.parse import urljoin

from services.ssc_client import BASE_URL, ATTACHMENT_BASE, is_allowed_url

# ---------------------------------------------------------------- JSON list
_LIST_KEYS = ("data", "items", "rows", "results", "notices", "noticeBoards", "content")


def extract_items(payload, _depth=0):
    """Finds the list of notice dicts inside whatever wrapper the API uses."""
    if isinstance(payload, list):
        if all(isinstance(x, dict) for x in payload):
            return payload
        return []
    if isinstance(payload, dict) and _depth < 4:
        for key in _LIST_KEYS:
            if key in payload:
                found = extract_items(payload[key], _depth + 1)
                if found or isinstance(payload[key], list):
                    return found
        for value in payload.values():
            if isinstance(value, (dict, list)):
                found = extract_items(value, _depth + 1)
                if found:
                    return found
    return []


# ----------------------------------------------------------------- dates
_MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], 1)}
for _full, _n in list(_MONTHS.items()):
    _MONTHS[_full[:3]] = _n
_MONTHS["sept"] = 9


def _valid(d):
    """A date is accepted only if it is in a sensible range."""
    if d is None:
        return None
    today = date.today()
    if date(2000, 1, 1) <= d <= date(today.year + 3, 12, 31):
        return d
    return None


def parse_date(value):
    """Reads ISO, dd-mm-yyyy and '22 June 2026' styles. Returns date or None."""
    if not value or not isinstance(value, str):
        return None
    s = value.strip()
    try:
        return _valid(datetime.fromisoformat(s.replace("Z", "+00:00")).date())
    except ValueError:
        pass
    m = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", s)
    if m:
        try:
            return _valid(date(int(m[3]), int(m[2]), int(m[1])))
        except ValueError:
            return None
    m = re.match(r"^(\d{1,2})(?:st|nd|rd|th)?[\s,-]+([A-Za-z]{3,9})\.?[\s,-]+(\d{4})", s)
    if m and m[2].lower() in _MONTHS:
        try:
            return _valid(date(int(m[3]), _MONTHS[m[2].lower()], int(m[1])))
        except ValueError:
            return None
    return None


# ------------------------------------------------------------ attachments
def build_attachment_url(redirect_url):
    """Builds a full PDF address. Returns None unless it is on ssc.gov.in."""
    if not redirect_url or not isinstance(redirect_url, str):
        return None
    r = redirect_url.strip()
    if r.lower().startswith("http"):
        url = r
    elif r.startswith("/"):
        url = urljoin(BASE_URL, r)
    elif r.lower().endswith(".pdf"):
        url = ATTACHMENT_BASE + r
    else:
        return None
    return url if is_allowed_url(url) else None


# --------------------------------------------------------- exam detection
_EXAM_PATTERNS = [
    ("CHSL", r"combined higher secondary|\bchsl\b"),
    ("CGL", r"combined graduate level|\bcgl\b"),
    ("MTS", r"multi[\s-]*tasking|\bmts\b"),
    ("GD", r"constable\s*\(?gd\)?|\bgd\b.*constable|general duty"),
    ("CPO", r"sub[\s-]*inspector|\bcpo\b|central police organi[sz]ation"),
    ("JE", r"junior engineer|\bjse\b|\bje\b"),
    ("STENO", r"stenographer"),
    ("SELECTION_POST", r"selection post"),
    ("JHT", r"junior hindi translator|\bjht\b"),
]


def classify_exam(headline):
    # Treat underscores and hyphens as spaces in filenames too.
    text = re.sub(r"[_-]+", " ", (headline or "").lower())

    for code, pattern in _EXAM_PATTERNS:
        if re.search(pattern, text):
            return code

    return None


def normalize_item(item):
    """One API notice -> clean dict, or None if it has no usable headline/id."""
    headline = str(item.get("headline") or "").strip()
    if not headline:
        return None

    source_id = item.get("id")
    attachment = build_attachment_url(item.get("redirectUrl"))
    uid = str(source_id) if source_id not in (None, "") else (f"pdf:{attachment}" if attachment else None)
    if uid is None:
        return None

    return {
        "uid": uid,
        "headline": headline[:1000],
        "exam_id_raw": str(item.get("examId")) if item.get("examId") not in (None, "") else None,
        "exam_code": classify_exam(headline),
        "published_on": parse_date(item.get("createdAt")),
        "start_date": parse_date(item.get("startDate")),
        "end_date": parse_date(item.get("endDate")),
        "attachment_url": attachment,
    }


# ------------------------------------------------------------- PDF facts
_DATE_RE = (r"(\d{1,2}[-/.]\d{1,2}[-/.]\d{4}"
            r"|\d{1,2}(?:st|nd|rd|th)?[\s,-]+[A-Za-z]{3,9}\.?[\s,-]+\d{4})")

_LABELS = {
    "apply_start": r"(?:commencement|opening|start)[^.\n]{0,40}(?:submission|receipt|application)",
    "apply_end": r"last\s+date[^.\n]{0,60}(?:submission|receipt|application)[^.\n]{0,40}?",
}


def pdf_to_text(data):
    """Reads PDF bytes. Needs PyMuPDF (pip install pymupdf) or pdfplumber."""
    try:
        import fitz  # PyMuPDF
        with fitz.open(stream=data, filetype="pdf") as doc:
            return "\n".join(page.get_text() for page in doc)
    except ImportError:
        pass
    try:
        import io
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            return "\n".join((p.extract_text() or "") for p in pdf.pages)
    except ImportError:
        raise RuntimeError("Install PyMuPDF to read PDFs:  pip install pymupdf")


def extract_facts(text):
    """
    Conservative extraction. A value is returned only when it is found clearly
    and passes validation; otherwise it is left out (the app then shows
    'Not announced yet'). Returns (facts, notes).
    """
    facts, notes = {}, []
    flat = re.sub(r"[ \t]+", " ", text or "")

    for key, label in _LABELS.items():
        m = re.search(label + r"[^0-9A-Za-z]{0,40}?(?<!\d)" + _DATE_RE, flat, re.I)
        d = parse_date(m.group(1)) if m else None
        if d:
            facts[key] = d.isoformat()

    if "apply_start" in facts and "apply_end" in facts \
            and facts["apply_end"] < facts["apply_start"]:
        notes.append("Application end date was before the start date; both dropped.")
        facts.pop("apply_start"); facts.pop("apply_end")

    counts = set()
    for m in re.finditer(r"(\d{1,3}(?:,\d{3})+|\d{2,6})\s+(?:tentative\s+)?vacanc", flat, re.I):
        n = int(m.group(1).replace(",", ""))
        if 1 <= n <= 200000:
            counts.add(n)
    if len(counts) == 1:
        facts["vacancies"] = counts.pop()
    elif len(counts) > 1:
        notes.append(f"Several vacancy figures found {sorted(counts)}; not saved automatically.")

    fees = sorted({int(x) for x in re.findall(r"(?:Rs\.?|₹)\s*(\d{2,4})\s*/?-?", flat)})
    if fees:
        facts["fee_amounts_seen"] = fees[:6]

    return facts, notes
