"""
gui.py
------
Tkinter desktop UI for WebFIRE Deviation Scanner.
Zero extra dependencies beyond requests + beautifulsoup4.

Usage:
    python3 gui.py
"""

import csv
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import webfire_core as core

DOWNLOAD_DIR = Path(__file__).parent / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

# ── Colours ────────────────────────────────────────────────────────────────
C_HEADER   = "#1a3a5c"
C_BTN_BLUE = "#2563eb"
C_BTN_GRN  = "#16a34a"
C_BTN_AMB  = "#d97706"
C_DEV_BG   = "#ffe0e0"
C_DEV_FG   = "#990000"
C_ERR_BG   = "#fffbe6"
C_CACHED_BG= "#f0fff4"


# ══════════════════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WebFIRE Deviation Scanner")
        self.geometry("1100x820")
        self.minsize(900, 600)
        self.configure(bg="#f0f2f5")

        self._session  = None
        self._reports  = []   # list[dict] from last search
        self._selected = {}   # id -> bool (checkbox state)
        self._scan_rows = []

        self._build_ui()

    # ── UI construction ────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Force light theme so dark-mode macOS doesn't swallow field text
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TEntry",
                         fieldbackground="white", foreground="#111111",
                         insertcolor="#111111", bordercolor="#cbd5e1",
                         lightcolor="#cbd5e1", darkcolor="#cbd5e1")
        style.configure("TCombobox",
                         fieldbackground="white", foreground="#111111",
                         selectbackground="white", selectforeground="#111111",
                         bordercolor="#cbd5e1")
        style.map("TCombobox",
                  fieldbackground=[("readonly", "white")],
                  foreground=[("readonly", "#111111")])
        style.configure("Treeview",
                         background="white", foreground="#111111",
                         fieldbackground="white", rowheight=22)
        style.configure("Treeview.Heading",
                         background="#eef1f5", foreground="#1e293b",
                         font=("Helvetica", 9, "bold"), relief="flat")
        style.map("Treeview",
                  background=[("selected", "#2563eb")],
                  foreground=[("selected", "white")])
        style.configure("TScrollbar",
                         troughcolor="#e2e8f0", background="#94a3b8")
        style.configure("Horizontal.TProgressbar",
                         troughcolor="#e2e8f0", background="#16a34a")
        style.configure("TProgressbar",
                         troughcolor="#e2e8f0", background="#16a34a")

        # ── Title bar
        hdr = tk.Frame(self, bg=C_HEADER, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="WebFIRE Deviation Scanner",
                 bg=C_HEADER, fg="white",
                 font=("Helvetica", 15, "bold")).pack(side="left", padx=16, pady=10)
        tk.Label(hdr, text="EPA CDX / WebFIRE Report Search & Analysis",
                 bg=C_HEADER, fg="#93b8d8",
                 font=("Helvetica", 10)).pack(side="left", padx=4, pady=10)

        # ── Scrollable main canvas
        outer = tk.Frame(self, bg="#f0f2f5")
        outer.pack(fill="both", expand=True)
        self._canvas = tk.Canvas(outer, bg="#f0f2f5", highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._main = tk.Frame(self._canvas, bg="#f0f2f5", padx=16, pady=12)
        self._canvas_win = self._canvas.create_window(
            (0, 0), window=self._main, anchor="nw")

        self._main.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # ── Steps
        self._build_search_section()
        self._build_results_section()
        self._build_download_section()
        self._build_scan_section()

        # ── Status bar
        self._status_var = tk.StringVar(value="Ready")
        sb = tk.Frame(self, bg="#e2e8f0", height=26)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)
        tk.Label(sb, textvariable=self._status_var,
                 bg="#e2e8f0", fg="#475569",
                 font=("Helvetica", 10), anchor="w").pack(
                     side="left", padx=10, pady=3)

    def _section_header(self, parent, step, title):
        f = tk.Frame(parent, bg=C_HEADER)
        f.pack(fill="x")
        badge = tk.Label(f, text=str(step), bg="#2d6a9f", fg="white",
                         font=("Helvetica", 10, "bold"),
                         width=2, relief="flat")
        badge.pack(side="left", padx=(8, 6), pady=6)
        tk.Label(f, text=title, bg=C_HEADER, fg="white",
                 font=("Helvetica", 10, "bold")).pack(side="left", pady=6)
        return f

    def _card(self, parent, step, title, hidden=False):
        outer = tk.Frame(parent, bg="#f0f2f5")
        outer.pack(fill="x", pady=(0, 12))
        self._section_header(outer, step, title)
        body = tk.Frame(outer, bg="white",
                        relief="flat", bd=0,
                        highlightbackground="#dde1e7",
                        highlightthickness=1)
        body.pack(fill="x")
        if hidden:
            outer.pack_forget()
        return outer, body

    # ── Step 1: Search ─────────────────────────────────────────────────────

    def _build_search_section(self):
        _, body = self._card(self._main, 1, "SEARCH PARAMETERS")
        body.configure(padx=14, pady=12)

        # Row 0
        r0 = tk.Frame(body, bg="white")
        r0.pack(fill="x", pady=(0, 8))

        self._fac_var  = self._labeled_entry(r0, "Facility Name", 0, width=22)
        self._org_var  = self._labeled_entry(r0, "Organization", 1, width=22)

        # State dropdown
        tk.Label(r0, text="State", bg="white", fg="#111111",
                 font=("Helvetica", 9, "bold")).grid(row=0, column=4, sticky="w", padx=(12, 4))
        self._state_var = tk.StringVar(value="AA")
        state_cb = ttk.Combobox(r0, textvariable=self._state_var, width=22,
                                state="readonly")
        state_cb["values"] = [f"{v}  —  {l}" for v, l in core.STATE_OPTIONS]
        state_cb.current(0)
        state_cb.grid(row=1, column=4, padx=(12, 4), sticky="w")

        self._city_var = self._labeled_entry(r0, "City", 5, width=14)

        # Row 1
        r1 = tk.Frame(body, bg="white")
        r1.pack(fill="x", pady=(0, 8))

        self._zip_var   = self._labeled_entry(r1, "ZIP Code",   0, width=12)
        self._start_var = self._labeled_entry(r1, "Start Date (MM/DD/YYYY)", 1, width=16)
        self._end_var   = self._labeled_entry(r1, "End Date (MM/DD/YYYY)",   2, width=16)

        # CFR Part
        tk.Label(r1, text="CFR Part", bg="white", fg="#111111",
                 font=("Helvetica", 9, "bold")).grid(row=0, column=5, sticky="w", padx=(12, 4))
        self._cfrpart_var = tk.StringVar(value="All")
        cfr_cb = ttk.Combobox(r1, textvariable=self._cfrpart_var, width=22, state="readonly")
        cfr_cb["values"] = [l for _, l in core.CFR_PART_OPTIONS]
        cfr_cb.current(0)
        cfr_cb.grid(row=1, column=5, padx=(12, 4), sticky="w")

        self._cfrsub_var = self._labeled_entry(r1, "CFR Subpart", 6, width=12)

        # Button row
        btn_row = tk.Frame(body, bg="white")
        btn_row.pack(fill="x", pady=(4, 0))
        self._btn_search = tk.Button(
            btn_row, text="  Search WebFIRE  ",
            bg=C_BTN_BLUE, fg="white", activebackground="#1d4ed8",
            font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2",
            padx=6, pady=5, command=self._do_search)
        self._btn_search.pack(side="left")
        self._search_lbl = tk.Label(btn_row, text="", bg="white",
                                    fg="#374151", font=("Helvetica", 9))
        self._search_lbl.pack(side="left", padx=12)

    def _labeled_entry(self, parent, label, col, width=18):
        tk.Label(parent, text=label, bg="white", fg="#111111",
                 font=("Helvetica", 9, "bold")).grid(
                     row=0, column=col*2, sticky="w", padx=(0 if col == 0 else 12, 4))
        var = tk.StringVar()
        e = tk.Entry(parent, textvariable=var, width=width,
                     bg="white", fg="#111111", insertbackground="#111111",
                     relief="solid", bd=1,
                     highlightthickness=1, highlightcolor="#2563eb",
                     highlightbackground="#cbd5e1",
                     font=("Helvetica", 10))
        e.grid(row=1, column=col*2, padx=(0 if col == 0 else 12, 4), sticky="w")
        return var

    # ── Step 2: Results ────────────────────────────────────────────────────

    def _build_results_section(self):
        self._results_card, body = self._card(
            self._main, 2, "SEARCH RESULTS", hidden=True)
        body.configure(padx=0, pady=0)

        # Toolbar
        tb = tk.Frame(body, bg="#f8fafc", pady=6, padx=10)
        tb.pack(fill="x")
        self._res_count_lbl = tk.Label(tb, text="", bg="#f8fafc",
                                       fg="#111111", font=("Helvetica", 9))
        self._res_count_lbl.pack(side="left")
        tk.Button(tb, text="Select All", bg="#e5e7eb", relief="flat",
                  font=("Helvetica", 9), cursor="hand2", padx=6,
                  command=self._select_all).pack(side="left", padx=(12, 4))
        tk.Button(tb, text="Clear", bg="#e5e7eb", relief="flat",
                  font=("Helvetica", 9), cursor="hand2", padx=6,
                  command=self._select_none).pack(side="left", padx=4)
        self._btn_download = tk.Button(
            tb, text="  \u2193  Download Selected  ",
            bg=C_BTN_GRN, fg="white", activebackground="#15803d",
            font=("Helvetica", 9, "bold"), relief="flat", cursor="hand2",
            padx=6, pady=3, command=self._do_download)
        self._btn_download.pack(side="right", padx=6)

        # Treeview
        cols = ("chk", "facility", "org", "city", "st",
                "date", "type", "subtype", "pollutants", "status")
        self._res_tree = ttk.Treeview(
            body, columns=cols, show="headings", height=10, selectmode="none")

        widths = {"chk": 28, "facility": 200, "org": 180, "city": 100,
                  "st": 36, "date": 100, "type": 52, "subtype": 70,
                  "pollutants": 160, "status": 90}
        heads  = {"chk": "", "facility": "Facility", "org": "Organization",
                  "city": "City", "st": "St", "date": "Date",
                  "type": "Type", "subtype": "Sub", "pollutants": "Pollutants",
                  "status": "Status"}
        for c in cols:
            self._res_tree.heading(c, text=heads[c])
            self._res_tree.column(c, width=widths[c],
                                  stretch=(c in ("facility", "org", "pollutants")))

        self._res_tree.tag_configure("cached", background=C_CACHED_BG)

        vsb2 = ttk.Scrollbar(body, orient="vertical",
                              command=self._res_tree.yview)
        self._res_tree.configure(yscrollcommand=vsb2.set)
        self._res_tree.pack(side="left", fill="both", expand=True)
        vsb2.pack(side="right", fill="y")

        self._res_tree.bind("<ButtonRelease-1>", self._toggle_checkbox)

    # ── Step 3: Download progress ──────────────────────────────────────────

    def _build_download_section(self):
        self._dl_card, body = self._card(
            self._main, 3, "DOWNLOAD PROGRESS", hidden=True)
        body.configure(padx=14, pady=10)

        prog_row = tk.Frame(body, bg="white")
        prog_row.pack(fill="x", pady=(0, 6))
        self._dl_bar = ttk.Progressbar(prog_row, mode="determinate", length=500)
        self._dl_bar.pack(side="left", fill="x", expand=True)
        self._dl_lbl = tk.Label(prog_row, text="", bg="white",
                                fg="#111111", font=("Helvetica", 9), width=10)
        self._dl_lbl.pack(side="left", padx=8)

        log_frame = tk.Frame(body, bg="white")
        log_frame.pack(fill="x")
        self._dl_log = tk.Text(log_frame, height=5, state="disabled",
                               bg="#f8fafc", fg="#111111",
                               font=("Courier", 9), relief="flat",
                               wrap="none", borderwidth=0,
                               insertbackground="#111111")
        dl_log_vsb = ttk.Scrollbar(log_frame, orient="vertical",
                                   command=self._dl_log.yview)
        self._dl_log.configure(yscrollcommand=dl_log_vsb.set)
        self._dl_log.pack(side="left", fill="both", expand=True)
        dl_log_vsb.pack(side="right", fill="y")

    # ── Step 4: Scan ───────────────────────────────────────────────────────

    def _build_scan_section(self):
        self._scan_card, body = self._card(
            self._main, 4, "DEVIATION SCAN", hidden=True)
        body.configure(padx=0, pady=0)

        # Toolbar
        tb = tk.Frame(body, bg="#f8fafc", pady=6, padx=10)
        tb.pack(fill="x")
        self._btn_scan = tk.Button(
            tb, text="  \U0001f50d  Scan for Deviations  ",
            bg=C_BTN_AMB, fg="white", activebackground="#b45309",
            font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2",
            padx=6, pady=4, command=self._do_scan)
        self._btn_scan.pack(side="left")
        self._btn_export = tk.Button(
            tb, text="  Export CSV  ",
            bg="#e5e7eb", fg="#374151", relief="flat",
            font=("Helvetica", 9), cursor="hand2", padx=6, pady=4,
            command=self._do_export, state="disabled")
        self._btn_export.pack(side="left", padx=8)
        self._scan_count_lbl = tk.Label(tb, text="", bg="#f8fafc",
                                        fg="#111111", font=("Helvetica", 9))
        self._scan_count_lbl.pack(side="left", padx=12)

        # Scan progress bar (hidden until scan runs)
        self._scan_prog_frame = tk.Frame(body, bg="white", padx=14, pady=6)
        self._scan_prog_frame.pack(fill="x")
        self._scan_prog_frame.pack_forget()
        sp_row = tk.Frame(self._scan_prog_frame, bg="white")
        sp_row.pack(fill="x")
        self._scan_bar = ttk.Progressbar(sp_row, mode="determinate", length=500)
        self._scan_bar.pack(side="left", fill="x", expand=True)
        self._scan_lbl = tk.Label(sp_row, text="", bg="white",
                                  fg="#111111", font=("Helvetica", 9), width=12)
        self._scan_lbl.pack(side="left", padx=8)

        # Summary label
        self._scan_summary = tk.Label(body, text="", bg="white",
                                      font=("Helvetica", 10, "bold"),
                                      anchor="w", padx=14, pady=4)
        self._scan_summary.pack(fill="x")
        self._scan_summary.pack_forget()

        # Results treeview
        scols = ("result", "facility", "st", "date", "type",
                 "location", "pollutant", "measured", "limit",
                 "pct", "unit", "regulation", "notes")
        self._scan_tree = ttk.Treeview(
            body, columns=scols, show="headings", height=14)

        sheads = {"result": "Result", "facility": "Facility", "st": "St",
                  "date": "Date", "type": "Type", "location": "Location",
                  "pollutant": "Pollutant", "measured": "Measured",
                  "limit": "Limit", "pct": "% of Lim",
                  "unit": "Unit", "regulation": "Regulation", "notes": "Notes"}
        swidths = {"result": 80, "facility": 180, "st": 36, "date": 90,
                   "type": 52, "location": 70, "pollutant": 160,
                   "measured": 80, "limit": 70, "pct": 68,
                   "unit": 140, "regulation": 140, "notes": 160}
        for c in scols:
            self._scan_tree.heading(c, text=sheads[c])
            self._scan_tree.column(
                c, width=swidths[c],
                stretch=(c in ("facility", "pollutant", "unit", "regulation", "notes")))

        self._scan_tree.tag_configure("deviation",
                                      background=C_DEV_BG, foreground=C_DEV_FG)
        self._scan_tree.tag_configure("error",    background=C_ERR_BG)
        self._scan_tree.tag_configure("nolimit",  foreground="#6b7280")

        scan_vsb = ttk.Scrollbar(body, orient="vertical",
                                 command=self._scan_tree.yview)
        scan_hsb = ttk.Scrollbar(body, orient="horizontal",
                                 command=self._scan_tree.xview)
        self._scan_tree.configure(yscrollcommand=scan_vsb.set,
                                  xscrollcommand=scan_hsb.set)
        self._scan_tree.pack(side="left", fill="both", expand=True)
        scan_vsb.pack(side="right", fill="y")

        self._scan_placeholder = tk.Label(
            body,
            text="Click  Scan for Deviations  to analyze all downloaded reports.",
            bg="white", fg="#9ca3af", font=("Helvetica", 10), pady=16)
        self._scan_placeholder.pack()

    # ── Canvas / scroll helpers ────────────────────────────────────────────

    def _on_frame_configure(self, _e):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, e):
        self._canvas.itemconfig(self._canvas_win, width=e.width)

    def _on_mousewheel(self, e):
        self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    # ── Checkbox helpers ───────────────────────────────────────────────────

    def _toggle_checkbox(self, event):
        region = self._res_tree.identify_region(event.x, event.y)
        col    = self._res_tree.identify_column(event.x)
        iid    = self._res_tree.identify_row(event.y)
        if region != "cell" or not iid:
            return
        if col == "#1":  # checkbox column
            self._selected[iid] = not self._selected.get(iid, False)
            self._refresh_checkbox(iid)

    def _refresh_checkbox(self, iid):
        vals = list(self._res_tree.item(iid, "values"))
        vals[0] = "\u2611" if self._selected.get(iid) else "\u2610"
        self._res_tree.item(iid, values=vals)

    def _select_all(self):
        for iid in self._res_tree.get_children():
            self._selected[iid] = True
            self._refresh_checkbox(iid)

    def _select_none(self):
        for iid in self._res_tree.get_children():
            self._selected[iid] = False
            self._refresh_checkbox(iid)

    # ── Status helpers ─────────────────────────────────────────────────────

    def _set_status(self, msg):
        self._status_var.set(msg)

    def _show_card(self, card_outer):
        card_outer.pack(fill="x", pady=(0, 12))

    # ─────────────────────────────────────────────────────────────────────
    # Actions
    # ─────────────────────────────────────────────────────────────────────

    # ── Search ─────────────────────────────────────────────────────────────

    def _do_search(self):
        self._btn_search.configure(state="disabled", text="  Searching…  ")
        self._search_lbl.configure(text="")
        self._set_status("Connecting to WebFIRE…")

        def worker():
            try:
                if self._session is None:
                    self._session = core.build_session()
                params = {
                    "facility":   self._fac_var.get().strip(),
                    "organization": self._org_var.get().strip(),
                    "state":      self._state_var.get().split("  —  ")[0].strip(),
                    "city":       self._city_var.get().strip(),
                    "zip":        self._zip_var.get().strip(),
                    "startdate":  self._start_var.get().strip(),
                    "enddate":    self._end_var.get().strip(),
                    "CFRpart":    _cfr_value(self._cfrpart_var.get()),
                    "CFRSubpart": self._cfrsub_var.get().strip(),
                }
                reports = core.search(self._session, params)
                self.after(0, lambda: self._on_search_done(reports))
            except Exception as exc:
                self.after(0, lambda: self._on_search_error(str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_search_done(self, reports):
        self._reports  = reports
        self._selected = {}

        # Populate tree
        self._res_tree.delete(*self._res_tree.get_children())
        for r in reports:
            cached = (DOWNLOAD_DIR / f"{r['id']}.zip").exists()
            r["downloaded"] = cached
            chk   = "\u2611" if cached else "\u2610"
            iid   = self._res_tree.insert(
                "", "end",
                iid=r["id"],
                values=(chk,
                        r["facility"], r["organization"],
                        r["city"], r["state"],
                        r["date"][:10],
                        r["report_type"], r["report_subtype"],
                        r["pollutants"][:60],
                        "Downloaded" if cached else "Pending"),
                tags=("cached",) if cached else ())
            self._selected[iid] = cached  # pre-select cached rows

        n = len(reports)
        self._res_count_lbl.configure(
            text=f"{n} report{'s' if n != 1 else ''} found")
        self._search_lbl.configure(
            text=f"{n} result{'s' if n != 1 else ''}", fg="#16a34a")
        self._btn_search.configure(state="normal",
                                   text="  Search WebFIRE  ")
        self._set_status(f"Search complete — {n} reports found")
        self._show_card(self._results_card)
        self._show_card(self._dl_card)
        self._show_card(self._scan_card)

    def _on_search_error(self, msg):
        self._session = None   # force session rebuild next time
        self._btn_search.configure(state="normal",
                                   text="  Search WebFIRE  ")
        self._search_lbl.configure(text="Search failed", fg="#dc2626")
        self._set_status(f"Error: {msg}")
        messagebox.showerror("Search Failed", msg)

    # ── Download ───────────────────────────────────────────────────────────

    def _do_download(self):
        ids = [iid for iid, sel in self._selected.items() if sel]
        if not ids:
            messagebox.showinfo("Nothing selected",
                                "Check at least one report to download.")
            return

        by_id    = {r["id"]: r for r in self._reports}
        targets  = [by_id[i] for i in ids if i in by_id]
        if not targets:
            return

        self._btn_download.configure(state="disabled")
        self._dl_bar["maximum"] = len(targets)
        self._dl_bar["value"]   = 0
        self._dl_lbl.configure(text=f"0 / {len(targets)}")
        self._dl_log.configure(state="normal")
        self._dl_log.delete("1.0", "end")
        self._dl_log.configure(state="disabled")
        self._set_status("Downloading reports…")

        def worker():
            session = self._session
            session.headers["Referer"] = core.BASE_URL + "eSearchResults.cfm"
            for rpt in targets:
                ok, path, msg = core.download_report(
                    session, rpt["id"], DOWNLOAD_DIR)
                label = "cached" if msg == "already cached" \
                    else ("ok" if ok else f"error: {msg}")
                icon  = "\u2713" if (ok and msg != "already cached") \
                    else ("\u21a9" if msg == "already cached" else "\u2717")
                self.after(0, lambda r=rpt, lbl=label, ic=icon:
                           self._on_dl_progress(r, lbl, ic))
                if ok and msg != "already cached":
                    time.sleep(0.8)
            self.after(0, self._on_dl_done)

        threading.Thread(target=worker, daemon=True).start()

    def _on_dl_progress(self, rpt, label, icon):
        done = int(self._dl_bar["value"]) + 1
        total = int(self._dl_bar["maximum"])
        self._dl_bar["value"] = done
        self._dl_lbl.configure(text=f"{done} / {total}")

        line = f"{icon}  {rpt['id']}  —  {rpt['facility']}  ({label})\n"
        self._dl_log.configure(state="normal")
        self._dl_log.insert("end", line)
        self._dl_log.see("end")
        self._dl_log.configure(state="disabled")

        # Update status cell in results tree
        if rpt["id"] in self._res_tree.get_children():
            vals = list(self._res_tree.item(rpt["id"], "values"))
            if label in ("ok", "cached"):
                vals[9] = "Downloaded"
                self._res_tree.item(rpt["id"], values=vals, tags=("cached",))
            elif label.startswith("error"):
                vals[9] = "Error"
                self._res_tree.item(rpt["id"], values=vals)

    def _on_dl_done(self):
        self._btn_download.configure(state="normal")
        total = int(self._dl_bar["maximum"])
        self._set_status(f"Download complete — {total} report{'s' if total != 1 else ''}")

    # ── Scan ───────────────────────────────────────────────────────────────

    def _do_scan(self):
        targets = [
            r for r in self._reports
            if (DOWNLOAD_DIR / f"{r['id']}.zip").exists()
        ]
        if not targets:
            messagebox.showinfo("Nothing to scan",
                                "Download at least one report first.")
            return

        self._btn_scan.configure(state="disabled")
        self._btn_export.configure(state="disabled")
        self._scan_rows = []
        self._scan_tree.delete(*self._scan_tree.get_children())
        self._scan_summary.pack_forget()
        self._scan_placeholder.pack_forget()
        self._scan_prog_frame.pack(fill="x")
        self._scan_bar["maximum"] = len(targets)
        self._scan_bar["value"]   = 0
        self._scan_lbl.configure(text=f"0 / {len(targets)}")
        self._set_status("Scanning reports…")

        def worker():
            for rpt in targets:
                path = DOWNLOAD_DIR / f"{rpt['id']}.zip"
                rows = core.scan_report(path, rpt)
                self.after(0, lambda r=rows, total=len(targets):
                           self._on_scan_progress(r, total))

            self.after(0, self._on_scan_done)

        threading.Thread(target=worker, daemon=True).start()

    def _on_scan_progress(self, new_rows, total):
        self._scan_rows.extend(new_rows)
        done = int(self._scan_bar["value"]) + 1
        self._scan_bar["value"] = done
        self._scan_lbl.configure(text=f"{done} / {total}")

        for row in new_rows:
            dev = row.get("deviation", "")
            if dev == "error":
                tag = "error"
            elif dev == "YES":
                tag = "deviation"
            elif dev == "no limit":
                tag = "nolimit"
            else:
                tag = ""

            result_label = {
                "YES":      "DEVIATION",
                "no":       "Pass",
                "no limit": "No Limit",
                "error":    "Error",
            }.get(dev, dev)

            pct = row.get("pct_of_limit", "")
            pct_str = f"{pct}%" if pct != "" else "—"

            self._scan_tree.insert(
                "", "end",
                values=(result_label,
                        row.get("facility", "")[:40],
                        row.get("state", ""),
                        str(row.get("date", ""))[:10],
                        row.get("report_type", ""),
                        row.get("location", ""),
                        row.get("pollutant", ""),
                        row.get("avg_measured", ""),
                        row.get("limit", "") or "—",
                        pct_str,
                        row.get("unit", ""),
                        row.get("regulation", ""),
                        row.get("error", "")),
                tags=(tag,) if tag else ())

        flagged = sum(1 for r in self._scan_rows if r.get("deviation") == "YES")
        n = len(self._scan_rows)
        self._scan_count_lbl.configure(
            text=f"{n} comparison{'s' if n != 1 else ''}  ·  "
                 f"{flagged} deviation{'s' if flagged != 1 else ''} flagged")

    def _on_scan_done(self):
        self._scan_prog_frame.pack_forget()
        flagged = sum(1 for r in self._scan_rows if r.get("deviation") == "YES")
        n = len(self._scan_rows)

        if flagged:
            msg   = f"\u26a0\ufe0f  {flagged} potential deviation{'s' if flagged != 1 else ''} flagged — review highlighted rows"
            color = C_DEV_FG
        else:
            msg   = f"\u2705  No deviations detected in {n} comparisons across all downloaded reports"
            color = "#15803d"

        self._scan_summary.configure(text=msg, fg=color)
        self._scan_summary.pack(fill="x")
        self._btn_scan.configure(state="normal")
        if self._scan_rows:
            self._btn_export.configure(state="normal")
        self._set_status(
            f"Scan complete — {n} comparisons, {flagged} flagged")

    # ── Export CSV ─────────────────────────────────────────────────────────

    def _do_export(self):
        if not self._scan_rows:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="deviations.csv",
            title="Save scan results")
        if not path:
            return
        fields = ["report_id", "facility", "city", "state", "date",
                  "report_type", "location", "pollutant", "unit",
                  "n_runs", "avg_measured", "limit", "pct_of_limit",
                  "regulation", "deviation", "error"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(self._scan_rows)
        self._set_status(f"Exported {len(self._scan_rows)} rows → {Path(path).name}")


# ── Helpers ────────────────────────────────────────────────────────────────

def _cfr_value(display: str) -> str:
    """Map display label back to form value."""
    for val, label in core.CFR_PART_OPTIONS:
        if label == display or val == display:
            return val
    return "All"


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
