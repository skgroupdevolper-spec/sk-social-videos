# Performance check: 2026-11-08

Data: Metricool getAnalyticsDataByMetrics, brand 7815878, 2026-11-01 → 2026-11-08 02:45 PT, metrics IGRE02/23/11/24, FBRE02/10/11/13, YTVP02/17/06/08, TKPO02/07/11/13.

| Platform | What Metricool returned | Reading |
|---|---|---|
| Facebook Reels | 8 reels (11-02 → 11-05): 23, 15, 12, 6, 5, 2, 1, 0 on the first metric; 0 on the second; 0–4 on the third | Unchanged from yesterday. No reels after 11-05 because nothing has published since. |
| Instagram Reels | 1 row: 11-02 reel, 0 / 0 / avg watch 20.6 s | Unchanged |
| YouTube Shorts | 7 Shorts (11-02 → 11-04) listed by title, no view numbers | Unchanged |
| TikTok | no rows | Metricool still isn't pulling TikTok post stats |

## Critical: Metricool account limit (getScheduledPosts, 2026-11-08 02:45 PT)
- **2026-11-07: all 8 posts failed** with "You have reached your Metricool account limit."
- That is 11-05 (6 of 8), 11-06 (8 of 8) and 11-07 (8 of 8). The last posts that went out were 11-05_v1 on TikTok and Facebook.
- Today's 8 posts are scheduled the same way and will very likely fail too until the owner upgrades the Metricool plan or frees quota.

## Leaning
- No new data, so there is nothing to learn about voice, layout or hooks yet. Keep videos short (29.1 s and 28.1 s) with a question or contrast in the first frame and voice from 0 s.
