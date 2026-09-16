# What Fortnite's Discover surfacing actually measures

Curated reference facts (not accumulated lessons — this doesn't change often), from
[Epic's official documentation](https://dev.epicgames.com/documentation/fortnite/how-discover-works-in-fortnite).

- **Average playtime**: average minutes per session over a period, capped at 120 minutes so
  outlier sessions don't distort it. Longer, sustained sessions signal quality.
- **Bounce rate**: the fraction of sessions shorter than a row-specific threshold, often
  **5 minutes**. This is the concrete reason "first 5 minutes" matters for Discover specifically,
  not just general player experience — a high bounce rate hurts visibility to new players, not
  just that one session.
- **Player retention**: the percentage of players who come back to the island over a period.
  Repeat visits (a reason to return, not just a reason to stay the first time) matter for this.
- **Qualified Play-Through Rate (QPTR)**: an engagement-weighted play-through metric — players
  who get deep into the experience count for more than players who barely qualify.
- **Secondary signals**: concurrent users (CCU) and unique users affect search ranking/row
  placement; social play (invites, party returns) is tracked too.
- **Key principle**: deep engagement can outperform a large audience — Discover re-evaluates
  islands continuously as new data comes in, so genuine content improvements translate into
  visibility gains, not just a one-time ranking snapshot.
