# URL Identity Diagnostic Rule v1.0

## Purpose
Prevent false indexing diagnoses when the user-supplied URL and the indexed URL differ only by a trailing slash.

## Required order
1. Read the requested article URL.
2. Read Search Console `matched_url` when supplied.
3. Compare canonical URL, Google-selected canonical, and redirect target when available.
4. Test both trailing-slash variants before concluding that the page is not indexed.
5. Separate technical indexing failure from ranking/evaluation loss.

## Decision rules
- `/1238` and `/1238/` are not automatically different articles.
- If the indexed or matched URL is the trailing-slash variant, treat it as the same resource unless evidence shows otherwise.
- A non-indexed alias must not be described as an indexing failure when the canonical variant is indexed.
- When the canonical variant is indexed but impressions collapse, prioritize ranking loss, site-wide evaluation change, algorithm update, demand change, or SERP competition.
- Ask the user only for the Google-selected canonical when supplied evidence cannot resolve the identity.

## User-facing language
Do not ask the user to choose whether a trailing slash should exist. WordPress, Hatena, the web server, redirects, and canonical settings normally determine it.
