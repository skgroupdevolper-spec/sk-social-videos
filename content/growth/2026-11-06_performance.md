# Performance check: 2026-11-06

Data: Metricool getAnalyticsDataByMetrics, brand 7815878, 2026-10-30 → 2026-11-06 02:45 PT, metrics IGRE02/23/11/24, FBRE02/10/11/13, YTVP02/17/06/08, TKPO02/07/11/13.

| Platform | What Metricool returned | Reading |
|---|---|---|
| Facebook Reels | 7 reels (11-02 → 11-04): 0–19 views each (19, 15, 12, 6, 5, 2, 0), 0 on the second metric, 0–4 on the third | Still very low. Best were the 11-02 posts (19 and 15). |
| Instagram Reels | 1 row: 0, 0, avg watch 20.6 s (the 11-02 v0 reel) | Other reels not returned this time |
| YouTube Shorts | 7 Shorts listed by title, no view numbers yet | Analytics lag |
| TikTok | no rows | Metricool still isn't pulling TikTok post stats |

The posts with voiceover (from 11-05_v2 on) have **no data yet**. 11-05_v2 never published (see below), so the first voiced videos to go out are today's.

## Critical: Metricool account limit
getScheduledPosts on 2026-11-06 shows **6 of the 8 posts for 2026-11-05 failed** with "You have reached your Metricool account limit." (11-05_v1 YouTube + Instagram; all 4 of 11-05_v2). Only 11-05_v1 TikTok and Facebook went out. This looks like the Metricool plan's post quota. The owner needs to upgrade the plan or free up quota. Nothing in the content can fix this.

## Leaning
- Keep hooks as a searchable question in the first frame ("Shopify or WooCommerce?") with voice from 0 s.
- Keep videos under ~31 s (today: 27.4 s and 31.0 s).
