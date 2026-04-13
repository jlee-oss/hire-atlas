# Source Count Incident - 2026-04-12

## Summary

The dashboard consumed a 172-row `master 탭` snapshot as if it were the complete current source, even though recent project context had expected a much larger posting population.

This was not a Google Sheet write from the dashboard sync path. The verified sync path uses the read-only Google Sheets scope and only writes local JSON artifacts.

## Evidence

- Current synced local source: `data/jobs.json`
- Current synced tab: `master 탭`
- Current synced source rows: `172`
- Current dashboard rows after board filtering: `158`
- Previous local pre-sync snapshot count: `213`
- Prior service-scope audit source row count: `284`
- Same spreadsheet `raw/detail 탭` rows with job keys: `423`
- Same spreadsheet `raw/detail 탭` distinct job keys: `403`
- Same spreadsheet `master 탭` distinct job keys: `172`
- `raw/detail 탭` distinct job keys not present in `master 탭`: `269`
- `runs 탭` records a `promote-staging` step with `promoted_job_count: 172`

## Root Cause

The immediate failure was a source contract failure: the dashboard sync treated `master 탭` as the authoritative source without validating that its row count still matched the expected posting population.

The deeper issue is that raw collection, staging promotion, service-scope filtering, and dashboard projection are currently too easy to conflate. A reduced promoted master can look like valid input unless explicit row-count and source-layer gates reject it.

## Corrective Action Added

`scripts/sync_sheet_snapshot.py` now supports:

- `--help` without accidentally running a sync.
- `--dry-run` for read-only validation without writing local artifacts.
- `--min-source-rows N` to reject suspiciously small source tabs.
- default shrink protection against large local source contractions.
- `--allow-shrink` only for explicitly confirmed intentional shrink events.

## Operating Rule

Do not accept a smaller `master 탭` as normal when the user or upstream run context indicates a larger posting population. First compare:

- raw/detail distinct job keys
- master/staging rows
- active/current rows
- service-scope included rows
- dashboard-rendered rows

Only after those layers are reconciled should model quality or clustering quality be judged.
