# Evidence Rules v1

These thresholds are initial conservative defaults and are not yet SEO-normalized.
They are versioned in Knowledge so Runtime does not embed business thresholds.

LOW_SAMPLE does not discard an observation. It records the evidence with a
`low_sample` flag so later layers may reduce confidence or defer diagnosis.
