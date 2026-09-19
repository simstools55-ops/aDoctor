# Vital Signs Engine

The engine creates one immutable Vital Profile containing seven signs:

- Visibility
- Traffic
- CTR Health
- Ranking Stability
- Freshness
- Competition Resilience
- Content Integrity

## Current availability

The first five can be calculated from Search Console and Metadata observations.
Competition Resilience and Content Integrity remain `UNAVAILABLE` until SERP and
Article Snapshot observations exist.

## Overall score

The overall score is the arithmetic mean of available signs only.
Unavailable signs are reported explicitly and are not treated as zero.

## LOW_SAMPLE

LOW_SAMPLE evidence lowers confidence and applies the Knowledge-defined score penalty.
