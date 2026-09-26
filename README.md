# nadim-raj.github.io

Personal site of Kazi Nadimul Haque — Business Intelligence leadership in retail prop trading.

Live at **https://nadim-raj.github.io**

Single static page: plain HTML and CSS, no build step, served by GitHub Pages.

## Figures

The FundedNext numbers on the About section are read from their public homepage by
`scripts/update_figures.py`, run weekly by a GitHub Action.

The source renders them as animated counters, so the page ships the real value next to a
zeroed placeholder. The script validates every value against a plausible range, refuses
any cumulative figure that appears to have fallen, and leaves the page untouched if the
source is unreachable or nothing parses. A stale number is a non-event; a zero or an
unsourceable one is not. Last-known values live in `data/fundednext.json`.
