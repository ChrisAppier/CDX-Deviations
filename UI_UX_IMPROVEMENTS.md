# UI/UX Improvement Suggestions

This document reviews the current `gui.py` implementation section by section and proposes specific, actionable improvements. Issues are rated **High / Medium / Low** by expected user impact.

---

## Section 1 — Search Parameters (Step 1)

### H1 — No input validation on date fields
**Current:** Labels say "MM/DD/YYYY" but nothing prevents users from typing garbage. Bad dates pass silently to the WebFIRE API, which may return an unexpected empty result or an uninformative error.  
**Fix:** Validate on search click — check that non-empty date fields match `\d{2}/\d{2}/\d{4}` and surface an inline error before firing the network request.

### H2 — State dropdown defaults to "AA"
**Current:** Combo defaults to `index 0`, which is `"AA  —  All States"`. The code "AA" is an internal sentinel that is not a real postal abbreviation; displaying it as the initial value looks like a bug.  
**Fix:** Change the displayed default to `"All States"` (or re-order so the blank/"All" entry uses an empty string label). Alternatively, default to the most commonly searched state.

### M3 — No "Clear / Reset" button
**Current:** Users who run several searches must manually erase every field to start fresh.  
**Fix:** Add a small "Clear" button next to "Search WebFIRE" that resets all fields to defaults (State → All, dates → blank, etc.).

### M4 — No loading spinner / progress while searching
**Current:** The Search button text changes to "Searching…" but the button is the only feedback. On slow connections the UI looks frozen.  
**Fix:** Add a `ttk.Progressbar` in indeterminate mode that runs while the network request is in flight, hidden otherwise.

### L5 — CFR Subpart field has no format hint
**Current:** Users unfamiliar with CFR may not know subparts are entered as letters (e.g., "NNNN", "LLL").  
**Fix:** Add placeholder ghost text or a small tooltip / label like `"e.g. NNNN"`.

---

## Section 2 — Search Results (Step 2)

### H6 — Full row click does not toggle selection
**Current:** `_toggle_checkbox` only reacts when `col == "#1"` (the checkbox column). Clicking the facility name or date does nothing.  
**Fix:** Remove the column guard so any cell click on a row toggles the checkbox. This matches standard list-selection UX.

### H7 — No sort on the results table
**Current:** Results appear in WebFIRE's natural order. There is no way to sort by date, state, or facility.  
**Fix:** Add column heading `command=` handlers like the scan treeview already has.

### M8 — "Already downloaded" highlight is easy to miss
**Current:** Cached rows get a subtle light-blue `C_CACHED_BG` background. The "Downloaded" text in the Status column is the only explicit label.  
**Fix:** Add a legend or tooltip near the table header explaining row coloring. Consider a more distinct indicator like a checkmark icon in the Status column alongside the text.

### M9 — No empty-results placeholder in the results table
**Current:** If a search returns 0 reports, the results card appears but the treeview is empty with no message.  
**Fix:** Show a centered label `"No reports found — try broadening your search criteria"` inside the results area when the list is empty.

### L10 — Download button gives no indication of file size
**Current:** Users select N reports and click Download with no estimate of download size or time.  
**Fix:** Show a count like `"Download 12 reports (est. ~24 MB)"` — the report IDs are known so you can use a rough per-report estimate from past downloads.

---

## Section 3 — Download Progress (Step 3)

### H11 — Download log has no horizontal scrollbar
**Current:** `wrap="none"` is set but no horizontal `Scrollbar` is packed for the log `Text` widget. Long facility names / error messages are truncated.  
**Fix:** Add `dl_log_hsb = ttk.Scrollbar(log_frame, orient="horizontal")` and wire it to `self._dl_log.xview`, then pack it below the text widget.

### M12 — Cancel UX is unclear about what happens next
**Current:** After clicking Cancel, the button grays out and the status says "Cancelling…". Users don't know the current file must finish before cancellation takes effect.  
**Fix:** Change the status message to `"Cancelling — finishing current file…"`. When done, report `"Cancelled after {done}/{total}"` more prominently (consider a short-lived info bar rather than just the status bar at the bottom).

### M13 — Progress bar does not show current file name
**Current:** The `X / Y` counter advances but there is no indication of which file is in progress.  
**Fix:** Update the label next to the counter to show `"Downloading: 81140594 — Acme Cement…"` (truncated to fit). This helps users see that activity is happening, especially for large files.

### L14 — Log area height is fixed at 5 lines
**Current:** `height=5` — with many downloads the user must scroll the log constantly.  
**Fix:** Make the log height dynamic or allow the user to resize it. Alternatively, increase the default to 8 lines.

---

## Section 4 — Deviation Scan (Step 4)

### H15 — No sort direction indicator on column headings
**Current:** Clicking a column heading sorts the scan results, but there is no ▲/▼ arrow to show which column is active or the current direction. Users can't tell the sort state at a glance.  
**Fix:** After sorting, update the heading text to append `" ▲"` or `" ▼"`. Reset all other headings to plain text.

### H16 — Scan button active even when nothing is downloaded
**Current:** "Scan for Deviations" is always enabled (section is always visible). Clicking it when no ZIPs exist shows a `messagebox.showinfo` error dialog.  
**Fix:** Disable "Scan for Deviations" at startup; enable it only after at least one file exists in `DOWNLOAD_DIR`. Re-check on window focus so the button reflects reality after a Scan Local Folder session.

### M17 — "Review PDF" label is inconsistent and misleading
**Current:** The filter dropdown and parent-row result say `"Review PDF"` but many manual-review rows are not PDFs (tune-up reports, OOOOb, process-params-only XMLs).  
**Fix:** Rename to `"Manual Review"` everywhere — filter dropdown, scan summary label, and the parent row result text. This is the correct description of what those rows require.

### M18 — No double-click / right-click action on scan results
**Current:** Rows are read-only; there is no way to open the source file, copy a value, or navigate to the WebFIRE page from inside the tool.  
**Fix:** Bind `<Double-1>` on scan rows to open the ZIP file's location in Finder/Explorer using `subprocess.Popen(["open", str(DOWNLOAD_DIR)])` (Mac) or the equivalent. Optionally bind `<Button-2>` / `<Button-3>` for a context menu with "Open folder", "Copy report ID", and "Open WebFIRE page" options.

### M19 — Filter "Search:" label gives no hint of what is searched
**Current:** Users may not know the text filter covers facility, citation, pollutant, sheet, location, description, and error fields.  
**Fix:** Replace the bare `"Search:"` label with a tooltip or change it to `"Search (facility, pollutant, notes):"`, or show a small `?` help icon with a tooltip listing the covered fields.

### M20 — Scan summary label position is easy to overlook
**Current:** The summary (`"⚠️ 5 potential deviations flagged…"`) appears between the filter bar and the treeview — it's sandwiched and may be scrolled out of view.  
**Fix:** Also mirror this message in the status bar at the bottom in persistent form (the status bar currently shows `"Scan complete — N findings, N flagged"` but the deviation breakdown is lost after the scan summary appears). Consider making the scan summary row taller with larger bold text.

### M21 — Export buttons visually identical disabled vs. enabled
**Current:** Disabled Export CSV and Export XLSX buttons use `bg="#e5e7eb"` — the same style as when enabled. The `state="disabled"` suppresses the cursor but the visual change is subtle.  
**Fix:** Use a different `fg` (e.g., `"#9ca3af"` disabled vs. `"#374151"` enabled) or an explicit `disabledforeground` to make the enabled/disabled state obvious without hovering.

### L22 — Mousewheel hijack
**Current:** `self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)` captures all scroll events globally. When the user's cursor is over the scan treeview or the download log, mousewheel still scrolls the outer canvas instead of the widget under the cursor.  
**Fix:** Switch to `bind_all` only when the canvas is the active scrollable, or bind at the canvas widget level and use `focus_set()` to direct events. A common pattern is `bind_all` with a check of `event.widget` to route scroll to the correct widget.

### L23 — XLSX "Manual Review" vs. filter "Review PDF" mismatch
**Current:** The XLSX tab is named `"Manual Review"` but the GUI filter dropdown says `"Review PDF"`. These are the same category with different names.  
**Fix:** See M17 — once "Review PDF" is renamed to "Manual Review" everywhere, this inconsistency disappears.

### L24 — Fallback warning label is right-aligned and easy to miss
**Current:** `self._fallback_lbl` is packed `side="right"` in the filter bar. On wide windows this is far from any other content and the amber warning text can be overlooked.  
**Fix:** Move the fallback warning to appear beneath the filter bar as a full-width notice strip (similar to a browser warning bar), so it is impossible to miss when present.

---

## General / Cross-Cutting

### H25 — Global keyboard shortcuts missing
**Current:** No keyboard shortcuts are defined. Power users must mouse to every button.  
**Fix:** Bind at minimum:
- `Enter` in search fields → trigger search
- `Ctrl+A` / `Cmd+A` → Select All in results table
- `Ctrl+S` / `Cmd+S` → Export CSV (when results are available)
- `Escape` → Cancel download (if in progress)

### M26 — Window title does not reflect state
**Current:** Title is always `"CDX Deviation Scanner"`.  
**Fix:** Update the title to include the last search context or scan result, e.g. `"CDX Deviation Scanner — 12 reports | 3 deviations"`. This helps users who have multiple sessions open or return to a minimized window.

### M27 — No "About" or help panel
**Current:** There is no version info, no explanation of what the tool does, and no guidance for first-time users.  
**Fix:** Add a small `?` or `Help` button in the title bar area that opens a modal with a one-paragraph description of the workflow (Search → Download → Scan) and a version string.

### L28 — Scrollable outer canvas vs. treeview interaction
**Current:** The outer canvas scrolls the entire page, but the scan treeview also has its own scrollbar. These two scroll areas can conflict — users sometimes intend to scroll the treeview but scroll the page instead.  
**Fix:** When the scan treeview is the focus widget, suppress outer canvas mousewheel handling. A `<Enter>`/`<Leave>` binding on the treeview to toggle canvas mousewheel binding is the standard Tkinter solution.

### L29 — No confirmation before overwriting an existing export file
**Current:** `filedialog.asksaveasfilename` warns when overwriting but only if the OS dialog does so (behavior varies). The save logic itself does not check.  
**Fix:** Rely on the OS dialog's built-in confirmation; this is already standard behavior on macOS. No code change needed — just a note that it is OS-dependent and fine as-is.

---

## Summary Priority List

| # | Issue | Impact |
|---|-------|--------|
| H1 | Date field validation | High |
| H2 | State dropdown "AA" default | High |
| H6 | Full row click toggles checkbox | High |
| H7 | Sort on search results | High |
| H11 | Download log horizontal scrollbar | High |
| H15 | Sort direction arrow on headings | High |
| H16 | Scan button disabled when nothing to scan | High |
| H25 | Global keyboard shortcuts | High |
| M3 | Search reset button | Medium |
| M4 | Search loading indicator | Medium |
| M8 | Cached-row indicator clarity | Medium |
| M9 | Empty results placeholder | Medium |
| M12 | Cancel UX messaging | Medium |
| M13 | Progress shows current file name | Medium |
| M17 | "Review PDF" → "Manual Review" rename | Medium |
| M18 | Double-click to open file/folder | Medium |
| M19 | Filter search hint | Medium |
| M20 | Summary label visibility | Medium |
| M21 | Export button disabled style | Medium |
| M26 | Window title reflects state | Medium |
| M27 | Help / About panel | Medium |
| L5 | CFR Subpart format hint | Low |
| L10 | Download size estimate | Low |
| L14 | Taller download log | Low |
| L22 | Mousewheel hijack fix | Low |
| L24 | Fallback warning placement | Low |
| L28 | Treeview vs. canvas scroll conflict | Low |
