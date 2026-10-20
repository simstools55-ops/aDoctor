# Integration Policy

## Source of truth and snapshots

This repository is the source of truth for shared editorial knowledge and cross-product platform contracts. Each product includes a validated snapshot of a specific released version.

## Platform orchestration

- SIMS-Blog-Manager is the workflow orchestrator and system of record.
- SBM issues CaseID and routes diagnosis and treatment requests.
- Doctor returns diagnosis, Treatment Plan, and Referral to SBM.
- Writer, Creator, and Merge return results to SBM.
- Specialist products do not directly mutate another product's records.

## Update procedure

1. Change shared knowledge or platform contracts in this repository.
2. Run shared repository tests.
3. Update VERSION, CHANGELOG, registries, and release notes.
4. Create a release tag.
5. Import a scoped snapshot into each affected product.
6. Run product-specific regression tests.
7. Release the affected products in dependency order.

For the minimum treatment loop, the preferred release order is:

```text
Shared -> Doctor -> SBM -> Writer -> integration test
```

## Prohibited practices

- Editing the same shared rule independently in Writer and Article Creator
- Automatically tracking unreleased Shared content from a product
- Skipping product regression tests after a Shared change
- Doctor directly dispatching Writer/Creator/Merge work
- Writer/Creator/Merge returning the official treatment result only to Doctor
- A specialist product authoritatively changing SBM Case state
