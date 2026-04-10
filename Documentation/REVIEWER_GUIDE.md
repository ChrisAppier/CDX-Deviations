# WebFIRE Deviation Scanner — Reviewer Guide

**What this tool does:** Searches EPA's WebFIRE database for stack test and compliance reports,
downloads them, and automatically scans for emission deviations. Your job is to check whether it
is finding the right things and missing nothing.

---

## Part 1 — Auditing for Accuracy

### Check flagged deviations (Result = DEVIATION)
Open the source report by double-clicking the row. Confirm:
- The measured value shown actually exceeds the limit shown
- The pollutant and emission unit match the report
- The regulation cited (e.g., 40 CFR 63.6150) is correct for this facility and report type

### Check passed results (Result = Pass)
Pick a few "Pass" rows and open their reports. Confirm:
- All tested pollutants appear in the results — nothing should be missing
- Measured values are actually at or below the limit
- If a pollutant shows "No Limit," verify that the regulation truly has no numeric limit for it

### Check Manual Review rows
These are reports the tool could not automatically assess. Open each one and ask:
- Is there actually a deviation in this document that the tool failed to detect?
- Does it require manual review for a legitimate reason (PDF-only, complex format), or should
  the tool have been able to read it automatically?

### Red flags to note
- A facility you know had a violation shows up as "Pass"
- A report shows far fewer findings than you would expect, suggesting the tool missed sheets
- Facility name, state, or date is wrong compared to the actual document

---

## Part 2 — Suggesting Improvements

When writing feedback, be as specific as possible. The more concrete the description, the more
directly it can be acted on. Use this structure:

**What I did:** *(the exact steps you took)*
**What I expected:** *(what the correct output should be)*
**What happened instead:** *(what the tool actually showed)*
**Example:** *(report ID, facility name, pollutant, or citation where you saw this)*

### Good example
> *"I opened report 81234567 (Acme Cement, TX). The scan showed Pass for PM, but the XML report
> shows a measured value of 0.045 lb/ton against a limit of 0.040 lb/ton — that should be a
> DEVIATION."*

### Less useful example
> *"The results look wrong for some Texas facilities."*

### Other helpful things to note
- If a deviation type the tool does not recognize comes up frequently, name the CFR citation
  (e.g., 40 CFR 63.XXXX) and describe where in the report the deviation data lives
- If the tool is slow, confusing, or requires too many steps to answer a basic question, describe
  the specific friction point
- If a column, label, or piece of information is missing from the output that you regularly need,
  say what it is and why you use it

---

*Send feedback with the report ID and, if possible, a screenshot or the downloaded ZIP file.*
