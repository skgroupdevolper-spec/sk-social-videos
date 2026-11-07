# Performance check: 2026-11-07

Data: Metricool getAnalyticsDataByMetrics, brand 7815878, 2026-10-31 → 2026-11-07 02:45 PT, metrics IGRE02/23/11/24, FBRE02/10/11/13, YTVP02/17/06/08, TKPO02/07/11/13.

| Platform | What Metricool returned | Reading |
|---|---|---|
| Facebook Reels | 8 reels (11-02 → 11-05): 23, 15, 12, 6, 5, 2, 1, 0 on the first metric; 0 on the second; 0–4 on the third | Still very low. Best is 11-02 20:03 (23). The 11-05_v1 reel (API integration, the first voiced FB post) has 1 so far. |
| Instagram Reels | 1 row: 11-02 reel, 0 / 0 / avg watch 20.6 s | Other reels not returned |
| YouTube Shorts | 7 Shorts listed by title, no view numbers | Analytics still lag or aren't exposed |
| TikTok | no rows | Metricool still isn't pulling TikTok post stats |

## Critical: Metricool account limit (getScheduledPosts, 2026-11-07 02:45 PT)
- **2026-11-06: all 8 posts failed** with "You have reached your Metricool account limit." Nothing from 11-06 went out on any platform.
- 2026-11-05: 6 of 8 failed (only v1 TikTok and v1 Facebook published).
- So the voiced videos have reached only 2 platforms once, and there is no data yet to judge voice, layout or hooks.
- The owner needs to upgrade the Metricool plan or free up quota. Today's posts are scheduled, but they will very likely fail the same way.

## Leaning
- No new signal, so keep it short (today 29.1 s and 28.7 s), with a searchable question in the first frame and voice from 0 s.
