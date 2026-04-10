# WebFIRE Deviation Scanner — User & Technical Guide

---

## Page 1 — Using the Application

The scanner walks users through four sequential steps. Each step unlocks the next.

---

### Step 1 — Search Parameters

Enter any combination of search criteria to query EPA's WebFIRE database. Available fields
include facility name, organization, state, city, ZIP code, date range, CFR Part (60, 62, or
63), and CFR Subpart. All fields are optional — leaving everything blank returns all available
reports. Dates must be entered in MM/DD/YYYY format; the tool validates this before sending the
search. Press Enter or click **Search WebFIRE** to run. A spinner appears while the query is
in flight.

---

### Step 2 — Search Results

Returned reports appear in a table showing facility name, organization, city, state, date, report
type (ST = Stack Test, AER = Annual Emissions Report), subpart, pollutants, and download status.
Click any column heading to sort. Click any row to toggle its selection checkbox. Reports already
downloaded from a previous session are highlighted in green and pre-selected.

Use **Select All** or **Clear** to manage the selection, then click **Download Selected** to
proceed.

---

### Step 3 — Download Progress

The tool downloads each selected report as a ZIP file from WebFIRE, with a short pause between
requests to avoid overloading the server. A progress bar, file counter, and log show what is
being downloaded in real time. The **Cancel** button stops after the current file finishes.
Downloaded ZIPs are saved to the `downloads/` folder inside the application directory and
cached — they do not need to be re-downloaded in future sessions.

---

### Step 4 — Deviation Scan

Click **Scan for Deviations** to analyze every downloaded ZIP in the `downloads/` folder. A
progress bar tracks each report as it is processed. Results appear in a hierarchical tree:

- **Parent rows** summarize each report — facility, date, type, and an overall result
  (DEVIATION / Manual Review / Pass / Error).
- **Child rows** show individual findings within that report — the specific pollutant or
  regulation, measured value, limit, percent of limit, and notes.

**Row colors:**

| Color | Meaning |
|-------|---------|
| Red | Deviation detected |
| Amber | Manual review required |
| Yellow | Processing error |
| White / Gray | Passing or no applicable limit found |

**Filtering:** Use the search bar to filter by facility, pollutant, citation, or notes text.
Use the **Show** dropdown to display only Deviations, Manual Review, Pass, or Errors. Click
any column heading to re-sort.

**Double-click** any row to extract and open the source document from the ZIP file.

**Scan Local Folder** allows scanning ZIPs from any directory — useful for analyzing files
downloaded in a prior session without repeating the search.

---

### Exporting Results

| Export Option | Output |
|---------------|--------|
| **Export CSV** | Findings matching the current **Show** filter in a single comma-separated file with 18 columns: report ID, facility, location, pollutant, measured value, limit, percent of limit, regulation, and notes. The default filename reflects the active filter (e.g., `deviations_filtered.csv`). Set **Show** to "All" before exporting to include every finding |
| **Export XLSX** | When **Show** is set to "All": a formatted Excel workbook with five tabs — Deviations, Manual Review, Errors, Pass, and All Results. When a specific filter is active: a single tab containing only the matching rows. Rows are color-coded, headers are frozen, and auto-filter is enabled |
| **Extract Files** | Copies source documents out of their ZIPs into a destination folder organized into three subfolders: `Deviations/`, `Manual Review/`, and `No Deviations/`. Each file is prefixed with its report ID |

---

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Enter | Run search |
| Cmd+A | Select all results |
| Cmd+S | Export CSV |
| Escape | Cancel download |

---
---

## Page 2 — How Deviation Detection Works

The scanner handles two structurally different report formats. The report type is determined by
inspecting the contents of the downloaded ZIP file.

---

### Report Type Classification

| Type | Indicator | Format |
|------|-----------|--------|
| **ST** — Stack Test | ZIP contains an `.xml` file | EPA WebFIRE XML schema |
| **AER** — Annual Emissions Report | ZIP contains an `.xlsx` or `.xlsm` file | EPA CEDRI Excel template |
| **PDF** | ZIP contains only `.pdf` files | No structured data; flagged for manual review |
| **Bad Download** | File is not a valid ZIP | WebFIRE returned a bare PDF or unrecognized file |

---

### Stack Tests (ST) — XML Format

Stack test reports contain two categories of structured data:

- **Regulatory limits** — each entry specifies a pollutant, numeric limit, unit of measure, and
  the CFR regulation it comes from.
- **Emission measurements** — each entry specifies a pollutant, run number, measured value, unit,
  and the emission source (stack or duct) it came from.

**Detection algorithm:**

1. All measurements are grouped by emission source, pollutant, and unit.
2. Individual test runs within each group are averaged.
3. The average is compared against the matching regulatory limit. Units are normalized before
   comparison (e.g., "grains/dscf corrected to 12% CO₂" is treated as equivalent to "gr/dscf").
4. If the average measured value **exceeds** the limit → **DEVIATION**.
5. If the average is **at or below** the limit → **Pass**.
6. If no matching limit is found for a pollutant → **No Limit** (noted in gray; not a violation).

Certain report structures are automatically routed to Manual Review rather than auto-assessed:
reports where emission data is embedded in a PDF attachment, and reports that contain only process
parameter measurements (temperature, pressure, flow) with no emission concentrations.

---

### Annual Emissions Reports (AER) — Excel/CEDRI Format

CEDRI compliance reports are standardized Excel templates submitted through EPA's CEDRI portal.
The scanning process has three phases.

**Phase 1 — Identify the regulation**

The tool reads the `CitationID` value from a fixed cell in the report's Welcome sheet (row 3,
column B). This code identifies which CFR regulation the report covers — for example,
`63.6150(a)` for industrial boilers or `60.5420a(b)` for NSPS OOOOa oil and gas facilities.

**Phase 2 — Route to the right worksheets**

Each CEDRI template organizes deviation data in specific, named worksheets. The tool maintains a
routing table mapping citation codes to the relevant sheet names. For example:

- `63.1354` (boilers/process heaters) → `Excess Emissions`, `Excess Emissions Summary`,
  `Malfunction Deviation Count`, `CMS Downtime Detail`
- `63.6150` (industrial/commercial/institutional boilers) → `Deviation_Limits`,
  `Deviation_Summary_Limits`, `Deviation_CEM_CPMS`, and others

If the CitationID is not in the routing table, the tool falls back to scanning any sheet whose
name contains keywords such as "deviat," "excess," "malfunction," or "downtime." Results from
this fallback are flagged with a warning in the interface.

**Phase 3 — Scan each target worksheet**

Within each target sheet, the tool locates the machine-readable header row (identified by a
standard anchor field such as `RecordId` or `EngineId` in column B). It then classifies the
sheet as one of two types:

- **Summary sheet** — contains numeric totals such as `TotalDeviationHrs`,
  `Number_of_Deviations`, or `CMSDowntimeDuration`. If any of these values are **greater than
  zero** → **DEVIATION**. If all are zero → **Pass**.
- **Event-level sheet** — contains one row per deviation event. If **any data rows exist** →
  **DEVIATION**. If the sheet is empty → **Pass**.

Template placeholder rows that begin with "e.g." are recognized and skipped automatically.

---

### Special Domain Logic

Two regulation types require calculation beyond simple threshold checks.

**Fenceline Monitoring (§63.655)**

Facilities near benzene emission sources must submit periodic air concentration readings from
perimeter monitors. The tool reads the Sample Results sheet, filters to "Regular Monitor" sampler
types, computes the **annual average benzene concentration** per monitor location, and compares
each to the regulatory action level of **9.0 µg/m³**. Any location exceeding this average is
flagged as a DEVIATION.

**Stationary Combustion Turbines (§60.4214 / §63.4214)**

Stationary engines used in non-emergency roles must not exceed **100 hours per year**. The tool
reads the Non-emergency Use sheet, parses start and end timestamps for each engine, sums total
operating hours per engine ID, and flags any engine exceeding the annual limit.

---

### Result Categories

| Result | Meaning |
|--------|---------|
| **DEVIATION** | Measured emission or operating parameter exceeded a regulatory limit |
| **Manual Review** | Tool could not automatically assess — human review of the source document required |
| **Pass** | All measured values were within limits |
| **No Limit** | Pollutant was tested but no matching regulatory limit was found in the report |
| **Error** | File could not be read or a required data structure was missing |
