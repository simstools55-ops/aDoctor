# Search Console 365-Day Acquisition

## Components

- `SearchConsoleProvider`: provider-neutral interface
- `GoogleSearchConsoleAdapter`: Google API adapter
- `SearchConsoleAcquisitionService`: date windows, retry, paging, status, and contract conversion

## Data windows

The acquisition end date is three days before the current date to avoid incomplete
Search Console data. Doctor derives 28-day, 90-day, and 365-day periods ending on the
same date.

## Failure handling

- COMPLETE: every component succeeded and data exists
- NO_DATA: every component succeeded but no data exists
- PARTIAL: one or more components failed
- FAILED: every component failed

No credentials are stored in the repository.
