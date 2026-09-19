# SIMS aDoctor v1.5.1-dev

- LOW_SAMPLE + structurally hard SERP now triggers `CLUSTER_OPPORTUNITY_CHECK` before low-priority closure.
- Added existing-content support and aCreator opportunity routes.
- New articles must have independent search intent/user value and pass cannibalization/SERP checks; thin link-only satellites are prohibited.
- Enforced workflow consistency: normal-close outcomes cannot simultaneously request WAIT/MONITOR.
