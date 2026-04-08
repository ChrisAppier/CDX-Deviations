# WebFIRE Deviation Scanner

A desktop tool for EPA enforcement staff to search, download, and scan compliance reports from EPA's [WebFIRE](https://cfpub.epa.gov/webfire/) database — with a focus on identifying deviations reported under 40 CFR Parts 60 and 63.

---

## What It Does

- **Search** WebFIRE's report database by facility name, organization, state, city, ZIP, date range, and CFR part/subpart
- **Download** report ZIPs directly from WebFIRE (Stack Test and Air Emissions Report formats)
- **Scan** downloaded reports for emission limit exceedances and deviation flags
- **Export** results to CSV for further analysis or case documentation

Currently supports Stack Test (ST) reports submitted via ERT. Air Emissions Report (AER) support — including semiannual compliance reports and deviation reports submitted via CEDRI — is under active development.

---

## Project Status

**Stack Tests (ST):** Working. Searches WebFIRE, downloads ERT-format ZIPs, parses XML emission run data, compares measured values against reported limits, and flags exceedances.

**Air Emissions Reports (AER):** In development. CEDRI templates vary significantly by regulatory citation and subpart. Work is ongoing to map template structures and build targeted parsers for deviation-relevant report types.

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
3. Click **Search WebFIRE** — results populate with report type, subtype, and download status
4. Select reports and click **Download Selected**
5. Click **Scan for Deviations** to analyze all downloaded reports
6. Review flagged rows (highlighted in red) and export to CSV if needed

Downloaded ZIPs are cached locally in the `downloads/` folder and reused on subsequent searches.

---

## Repository Structure

```
webfire_core.py   # Search, download, and scan logic
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
