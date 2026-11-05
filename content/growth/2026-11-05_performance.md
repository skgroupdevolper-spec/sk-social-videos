# Performance check — 2026-11-05 (why views are near zero)

Data: Metricool analytics, posts 2026-11-02 → 2026-11-04 (brand 7815878), pulled 2026-11-05 ~09:30 PT.

| Platform | What Metricool shows | Reading |
|---|---|---|
| Instagram Reels | 6 reels: views 0–2 each, reach 0–2, avg watch time 1.6–8 s (one 20.6 s), 0 likes/saves/shares | Viewers leave in the first seconds of a 33–38 s video |
| Facebook Reels | 7 reels: 0–15 views, reach 0, 0–4 s avg time watched, 0 likes | Same pattern |
| YouTube Shorts | Videos listed, views not yet reported (YouTube analytics usually lag 2–3 days) | Unknown yet |
| TikTok | No video rows returned yet | Unknown — check in TikTok app; Metricool may not be pulling TikTok post stats for this account |

## Likely causes (most important first)
1. **Weak first 3 seconds / low retention.** Silent text slides, no voice, no person, no movement in the first second. Platforms test each video with a small audience; when most people swipe within ~2 s, distribution stops. Instagram watch time 1.6–8 s confirms this.
2. **New, small accounts with no engagement history.** Brand switched from a personal profile to SK Developer on 2026-11-03; TikTok handle (@siyalking149) doesn't match the brand. Follower count is not the main factor, but early engagement (likes, comments, shares, saves) is — and it has been 0.
3. **No comments/replies activity.** Nobody is commenting, pinning comments or replying in the first hour after posting (manual, owner side).
4. **Topic is broad "business software".** Viewers searching for web development help don't see a specific, searchable problem in the hook.
5. **Posting volume vs quality.** 2 posts/day across 4 platforms with the same template look. Later (2026) recommends consistency (e.g. 3–5 Reels/week) and original, high-quality content over volume.
6. **12:00 PT slot = 1 AM Pakistan.** Fine for US/UK viewers, but nobody is awake on the Pakistan side to engage in the first hour.

Nobody can guarantee fast ranking; these are the levers we control.

## Changes made today (renderer + rules)
- English **voiceover** on every scene (offline Piper voice, `tools/voice/`), music ducked under the voice.
- **Burned-in subtitles** (3 styles), many people watch muted.
- **Icons** (25 line icons), **illustrated developer character** typing at a laptop (cartoon, not a real person), **search-typing** scene, **icon grid** scene.
- **Daily layout variants** (`layout`: cards solid/outline/glass, captions box/bar/outline, progress bottom/top, align).
- Hook rules: voice starts in the first 0.2 s; first frame must show the problem as a question; target 22–32 s.
- Topic focus: **web development first** (websites, WordPress, Shopify, WooCommerce, custom web apps, speed, SEO-ready builds, landing pages).
- 2026-11-05_v2 re-rendered with voice/subtitles/character/icons and swapped in Metricool before its 12:00 slot.

## Owner actions that would help most (manual, not done by Claude)
- Reply to every comment in the first hour; pin the suggested comment from each package.md.
- Add the WhatsApp links/buttons in content/profile-setup.md (all still ⏳).
- Consider renaming the TikTok handle to match SK Developer (account setting — owner decision).
- Optional: try Instagram **Trial Reels** (shown to non-followers first) — Metricool supports `TRIAL_REEL`; say if you want it.
- Optional: real footage of your own screen/projects or your own voice beats any synthetic voice; send clips if you have them.

## Sources
- Metricool analytics (IGRE, FBRE, YTVP, TKPO metrics).
- Later, "Instagram Reels algorithm": https://later.com/blog/instagram-reels-algorithm/ (watch time & replays, first three seconds, shares, original content, 3–5 Reels/week consistency, Trial Reels).
