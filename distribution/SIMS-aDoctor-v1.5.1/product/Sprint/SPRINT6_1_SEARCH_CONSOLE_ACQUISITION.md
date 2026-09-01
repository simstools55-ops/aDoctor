# Sprint6.1 — Search Console 365-Day Acquisition

## Included

- provider-neutral Search Console interface
- Google Search Console adapter
- 28, 90, and 365-day aggregate retrieval
- query-level paging up to policy limit
- retry for rate limit, timeout, and temporary failure
- COMPLETE, PARTIAL, FAILED, and NO_DATA states
- conversion to existing Observation input contract
- unit and integration tests

## Deployment requirement

A deployment environment must construct an authenticated Google Search Console service
and pass it to `GoogleSearchConsoleAdapter`.

## Excluded

- credential storage
- OAuth UI
- scheduler
- SERP acquisition
