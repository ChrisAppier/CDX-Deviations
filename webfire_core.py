"""
webfire_core.py
---------------
Core search / download / scan logic. Imported by gui.py.
"""

import warnings
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore")  # suppress LibreSSL urllib3 noise

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BASE_URL    = "https://cfpub.epa.gov/webfire/reports/"
DETAIL_URL  = "https://cfpub.epa.gov/webfire/FIRE/view/dspERTDocumentDetails.cfm"
_UA         = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/16.0 Safari/605.1.15"
)

STATE_OPTIONS = [
    ("AA", "All"), ("AL", "ALABAMA"), ("AK", "ALASKA"), ("AS", "AMERICAN SAMOA"),
    ("AZ", "ARIZONA"), ("AR", "ARKANSAS"), ("CA", "CALIFORNIA"), ("CO", "COLORADO"),
    ("CT", "CONNECTICUT"), ("DE", "DELAWARE"), ("DC", "DISTRICT OF COLUMBIA"),
    ("FL", "FLORIDA"), ("GA", "GEORGIA"), ("GU", "GUAM"), ("HI", "HAWAII"),
    ("ID", "IDAHO"), ("IL", "ILLINOIS"), ("IN", "INDIANA"), ("IA", "IOWA"),
    ("KS", "KANSAS"), ("KY", "KENTUCKY"), ("LA", "LOUISIANA"), ("ME", "MAINE"),
    ("MD", "MARYLAND"), ("MA", "MASSACHUSETTS"), ("MI", "MICHIGAN"),
    ("MN", "MINNESOTA"), ("MS", "MISSISSIPPI"), ("MO", "MISSOURI"), ("MT", "MONTANA"),
    ("NE", "NEBRASKA"), ("NV", "NEVADA"), ("NH", "NEW HAMPSHIRE"),
    ("NJ", "NEW JERSEY"), ("NM", "NEW MEXICO"), ("NY", "NEW YORK"),
    ("NC", "NORTH CAROLINA"), ("ND", "NORTH DAKOTA"),
    ("MP", "NORTHERN MARIANA ISLANDS"), ("OH", "OHIO"), ("OK", "OKLAHOMA"),
    ("OR", "OREGON"), ("PA", "PENNSYLVANIA"), ("PR", "PUERTO RICO"),
    ("RI", "RHODE ISLAND"), ("SC", "SOUTH CAROLINA"), ("SD", "SOUTH DAKOTA"),
    ("TN", "TENNESSEE"), ("TX", "TEXAS"), ("UT", "UTAH"), ("VT", "VERMONT"),
    ("VI", "VIRGIN ISLANDS"), ("VA", "VIRGINIA"), ("WA", "WASHINGTON"),
    ("WV", "WEST VIRGINIA"), ("WI", "WISCONSIN"), ("WY", "WYOMING"),
]

CFR_PART_OPTIONS = [
    ("All",     "All"),
    ("Part 60", "Part 60 — NSPS"),
    ("Part 62", "Part 62 — Federal Plan"),
    ("Part 63", "Part 63 — NESHAP"),
]


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

def build_session() -> requests.Session:
    """
    Establish a ColdFusion session with WebFIRE (3-step flow) and return
    a ready-to-use requests.Session.
    """
    s = requests.Session()
    s.headers["User-Agent"] = _UA
    s.headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"

    s.get(BASE_URL + "esearch.cfm", timeout=30)
    s.headers["Referer"] = BASE_URL + "esearch.cfm"
    s.post(BASE_URL + "esearch2.cfm",
           data={"reporttype": "All", "Submit": "Submit Search"},
           timeout=60)
    s.headers["Referer"] = BASE_URL + "esearch2.cfm"
    return s


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def search(session: requests.Session, params: dict) -> list:
    """
    POST the search form and return a list of report dicts.
    params keys: organization, facility, startdate, enddate, state,
                 county, city, zip, CFRpart, CFRSubpart
    """
    payload = {
        "organization": params.get("organization", ""),
        "facility":     params.get("facility",     ""),
        "startdate":    params.get("startdate",    ""),
        "enddate":      params.get("enddate",      ""),
        "state":        params.get("state",        "AA"),
        "county":       params.get("county",       ""),
        "city":         params.get("city",         ""),
        "zip":          params.get("zip",          ""),
        "CFRpart":      params.get("CFRpart",      "All"),
        "CFRSubpart":   params.get("CFRSubpart",   ""),
        "FRS":          "",
        "Submit":       "Submit Search",
    }
    r = session.post(BASE_URL + "eSearchResults.cfm", data=payload, timeout=60)
    r.raise_for_status()
    return _parse_results(r.text)


def _parse_results(html: str) -> list:
    soup  = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="cell-border")
    if not table:
        return []

    seen = {}
    for row in table.find_all("tr")[2:]:
        cells = row.find_all("td")
        if len(cells) < 11:
            continue
        link = cells[10].find("a", href=True)
        if not link or "ID=" not in link["href"]:
            continue

        doc_id = link["href"].split("ID=")[-1].strip()
        if doc_id not in seen:
            seen[doc_id] = {
                "id":             doc_id,
                "organization":   cells[0].get_text(strip=True),
                "facility":       cells[1].get_text(strip=True),
                "city":           cells[2].get_text(strip=True),
                "state":          cells[3].get_text(strip=True),
                "county":         cells[4].get_text(strip=True),
                "date":           cells[5].get_text(strip=True),
                "report_type":    cells[6].get_text(strip=True),
                "report_subtype": cells[7].get_text(strip=True),
                "pollutants":     cells[8].get_text(strip=True),
                "filename":       link.get("title", ""),
                "downloaded":     False,
                "scanned":        False,
            }
    return list(seen.values())


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def download_report(session: requests.Session, doc_id: str,
                    download_dir: Path) -> tuple:
    """
    Download a single report ZIP.
    Returns (success: bool, path: Path|None, error: str).
    """
    dest = download_dir / f"{doc_id}.zip"
    if dest.exists():
        return True, dest, "already cached"

    try:
        r = session.get(DETAIL_URL, params={"ID": doc_id}, timeout=120)
        r.raise_for_status()
        dest.write_bytes(r.content)
        return True, dest, ""
    except Exception as exc:
        return False, None, str(exc)


# ---------------------------------------------------------------------------
# Scan
# ---------------------------------------------------------------------------

def _elem_text(elem, tag: str) -> str:
    child = elem.find(tag)
    return (child.text or "").strip() if child is not None else ""


def _to_float(s: str):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def scan_report(local_path: Path, report_meta: dict) -> list:
    """
    Scan one report ZIP for emission vs. limit comparisons.
    Returns a list of finding dicts (one per pollutant+unit comparison).
    """
    try:
        outer = zipfile.ZipFile(local_path)
    except zipfile.BadZipFile:
        return [_error_row(report_meta, "Not a valid ZIP file")]

    xml_names = [n for n in outer.namelist() if n.endswith(".xml")]
    if not xml_names:
        # Note what file types ARE present
        exts = {Path(n).suffix.lower() for n in outer.namelist()}
        return [_error_row(report_meta, f"No XML found (contains: {', '.join(sorted(exts)) or 'nothing'})")]

    try:
        root = ET.fromstring(outer.read(xml_names[0]))
    except ET.ParseError as exc:
        return [_error_row(report_meta, f"XML parse error: {exc}")]

    # Regulatory limits keyed by (pds_id, poll_name, unit)
    limits = {}
    global_limits = {}  # (poll_name, unit) -> (regulation, limit)
    for elem in root.findall("qryEFRegs"):
        pds  = _elem_text(elem, "PDSid")
        poll = _elem_text(elem, "PollName")
        unit = _elem_text(elem, "EmissionUnit")
        lim  = _to_float(_elem_text(elem, "Limit"))
        reg  = _elem_text(elem, "Part_SubPart")
        if lim is not None:
            limits[(pds, poll, unit)] = lim
            if (poll, unit) not in global_limits:
                global_limits[(poll, unit)] = (reg, lim)

    # Per-run emission measurements
    runs = defaultdict(list)
    for elem in root.findall("qryEFEmis"):
        pds  = _elem_text(elem, "PDSid")
        loc  = _elem_text(elem, "Location")
        poll = _elem_text(elem, "PollName")
        unit = _elem_text(elem, "EmissionUnit")
        val  = _to_float(_elem_text(elem, "EmissionValue"))
        if val is not None:
            runs[(pds, loc, poll, unit)].append(val)

    if not runs:
        return [_error_row(report_meta, "No emission data in XML")]

    rows = []
    for (pds, loc, poll, unit), vals in runs.items():
        avg = sum(vals) / len(vals)

        lim = limits.get((pds, poll, unit))
        reg = ""
        if lim is None:
            match = global_limits.get((poll, unit))
            if match:
                reg, lim = match
        else:
            for elem in root.findall("qryEFRegs"):
                if (_elem_text(elem, "PDSid") == pds and
                        _elem_text(elem, "PollName") == poll and
                        _elem_text(elem, "EmissionUnit") == unit):
                    reg = _elem_text(elem, "Part_SubPart")
                    break

        rows.append({
            "report_id":    report_meta["id"],
            "facility":     report_meta["facility"],
            "city":         report_meta["city"],
            "state":        report_meta["state"],
            "date":         report_meta["date"],
            "report_type":  report_meta["report_type"],
            "location":     loc,
            "pollutant":    poll,
            "unit":         unit,
            "n_runs":       len(vals),
            "avg_measured": round(avg, 6),
            "limit":        lim if lim is not None else "",
            "pct_of_limit": round(avg / lim * 100, 1) if lim else "",
            "regulation":   reg,
            "deviation":    ("YES" if avg > lim else "no") if lim is not None else "no limit",
            "error":        "",
        })

    return rows


def _error_row(meta: dict, msg: str) -> dict:
    return {
        "report_id":    meta["id"],
        "facility":     meta["facility"],
        "city":         meta["city"],
        "state":        meta["state"],
        "date":         meta["date"],
        "report_type":  meta["report_type"],
        "location":     "",
        "pollutant":    "",
        "unit":         "",
        "n_runs":       "",
        "avg_measured": "",
        "limit":        "",
        "pct_of_limit": "",
        "regulation":   "",
        "deviation":    "error",
        "error":        msg,
    }
