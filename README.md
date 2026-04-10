# WebFIRE Deviation Scanner

A desktop tool for EPA enforcement staff to search, download, and scan compliance reports from EPA's [WebFIRE](https://cfpub.epa.gov/webfire/) database — with a focus on identifying deviations reported under 40 CFR Parts 60 and 63.

---

## What It Does

- **Search** WebFIRE's report database by facility name, organization, state, city, ZIP, date range, and CFR part/subpart
- **Download** report ZIPs directly from WebFIRE (Stack Test and Air Emissions Report formats)
- **Scan** downloaded reports for emission limit exceedances and deviation flags
- **Export** results to CSV or XLSX for further analysis or case documentation

---

## Project Status

**Stack Tests (ST):** Working. Searches WebFIRE, downloads ERT-format ZIPs, parses XML emission run data, compares measured values against reported limits, and flags exceedances.

**Air Emissions Reports (AER):** Working. Parses Excel-based CEDRI templates and routes to deviation-relevant sheets based on the CitationID embedded in each report. Supports 20+ CFR citations across Parts 60 and 63, including special-purpose logic for:

- **§63.655** — Fenceline benzene monitoring: computes annual average per sampler location and flags exceedances against the 9 µg/m³ action level
- **§60.4214 / §63.4214** — Stationary combustion turbines: sums non-emergency operating hours per engine and flags exceedances of the 100-hour annual limit
- **Summary and event-level sheets** — Detects non-zero deviation counts, durations, and percentages in CEDRI standard fields
- **Keyword fallback** — For citations not in the routing table, scans any sheet whose name contains deviation-related keywords (deviat, excess, malfunction, downtime)

Reports that require manual review (NSPS OOOOa/OOOOb leak records, tune-up reports) are flagged accordingly rather than auto-scanned.

---

## Installation

Requires Python 3.9+.

```bash
git clone https://github.com/YOUR_USERNAME/webfire-deviation-scanner.git
cd webfire-deviation-scanner
pip install -r requirements.txt
python gui.py
```

---

## Dependencies

```
requests
beautifulsoup4
openpyxl
```

---

## Usage

1. Launch the GUI with `python gui.py`
2. Enter search parameters (facility name, state, date range, CFR part, etc.)
3. Click **Search WebFIRE** — results populate with report type, subtype, and download status; previously downloaded reports are pre-selected and highlighted
4. Select reports and click **Download Selected**
5. Click **Scan for Deviations** to analyze all downloaded reports, or use **Scan Local Folder…** to scan a folder of ZIPs from a prior session
6. Review flagged rows (red = deviation, amber = manual review) and use the filter bar to narrow by facility, pollutant, or result type
7. Export to CSV or XLSX if needed

Downloaded ZIPs are cached locally in the `downloads/` folder and reused on subsequent searches.

**Keyboard shortcuts:** `Return` — search, `⌘A` — select all results, `⌘S` — export CSV, `Escape` — cancel download.

---

## Repository Structure

```
webfire_core.py   # Search, download, classify, and scan logic
gui.py            # Tkinter desktop UI
requirements.txt  # Python dependencies
downloads/        # Local cache of downloaded report ZIPs (gitignored)
```

---

## Background

WebFIRE is EPA's online repository for emission factors and compliance reports submitted via the Electronic Reporting Tool (ERT) and the Compliance and Emissions Data Reporting Interface (CEDRI). Stack test reports (submitted under 40 CFR Parts 60 and 63) and periodic Air Emissions Reports are publicly accessible through WebFIRE's report search interface.

This tool automates the pre-inspection research workflow of pulling and reviewing compliance documents for a facility or set of facilities, reducing time spent on manual document retrieval and initial screening.

---

## Notes

- This tool performs unauthenticated HTTP requests to the public WebFIRE interface. Use responsibly and avoid aggressive bulk downloading.
- Downloaded reports are cached locally. The `downloads/` directory is excluded from version control.
- This is an internal enforcement support tool and is not an official EPA product.
