# ScanSci PDF Browser Doctor Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a no-install browser doctor to ScanSci PDF so it follows the same shared browser runtime contract as ScanSci Find.

**Architecture:** Add a small standard-library resolver module under `src/scansci_pdf` that reports reusable browser options without installing anything. Expose it through Typer CLI and MCP while leaving existing download/login flows unchanged.

**Tech Stack:** Python 3.11, Typer, FastMCP, pytest/unittest-compatible tests.

---

### Task 1: Contract Tests

**Files:**
- Create: `tests/test_browser_doctor.py`

- [x] Write failing tests for resolver priority, JSON shape, no-install behavior, and shared data directories.
- [x] Write failing tests for CLI and MCP exposure.
- [x] Run targeted tests and confirm failures are caused by the missing doctor surface.

### Task 2: Resolver Implementation

**Files:**
- Create: `src/scansci_pdf/browser_discovery.py`

- [x] Implement injectable probes for deterministic tests.
- [x] Return `selected`, `source`, `available`, `install_needed`, `install_hint`, `profile_dir`, `cache_dir`, and `candidates`.
- [x] Probe configured command, `scansci-browser`, current ScanSci PDF browser modules, importable `cloakbrowser`/`playwright`, camofox HTTP endpoint, and system Chrome/Edge.

### Task 3: CLI And MCP Exposure

**Files:**
- Modify: `src/scansci_pdf/main.py`
- Modify: `src/scansci_pdf/server.py`
- Modify: `pyproject.toml`

- [x] Add `scansci-pdf browser-doctor`.
- [x] Add `scansci-pdf-browser` console script.
- [x] Add MCP tool `scansci_pdf_browser_doctor`.

### Task 4: Documentation

**Files:**
- Modify: `README.md`
- Modify: `skill/SKILL.md`

- [x] Document probe order, no-install behavior, and shared browser profile/cache directories.

### Task 5: Verification

**Commands:**
- `python -m pytest -q`
- `python -m scansci_pdf browser-doctor`
- `python -m scansci_pdf.browser_discovery`

- [x] Tests pass.
- [x] Doctor commands return JSON and do not install or start a browser.
