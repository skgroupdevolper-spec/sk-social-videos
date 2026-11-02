# Publishing rules

## Authorisation (owner, in chat, 2026-11-02)
- Platforms: all 4 — TikTok, YouTube Shorts, Facebook Reels, Instagram Reels — via Metricool brand 7815878 (connected accounts: Instagram @skgroupdevolper, Facebook Page, TikTok @siyalking149, YouTube channel).
- The owner explicitly asked for 2 videos per day to be made AND posted automatically. Daily runs schedule with autoPublish true. If the owner later says "approve each post", switch to autoPublish false (Metricool then sends a phone notification to publish by hand).
- Do not change any account settings, bios, buttons or passwords. Profile setup is the owner's manual job (content/profile-setup.md).

## Slots (America/Los_Angeles)
- Video 1: 06:00 (7 PM Pakistan, 9 AM New York, 2 PM London)
- Video 2: 12:00 (1 AM Pakistan, 3 PM New York, 8 PM London)
If a slot is less than 15 minutes away, use the next day's slot.

## How to schedule (from 2026-11-03)
Each video = **4 separate Metricool posts** (one provider each), so every platform gets its own text from package.md:
- TikTok: providers [tiktok]; text = TikTok caption; tiktokData {title, privacyOption "PUBLIC_TO_EVERYONE", commercialContentOwnBrand true}.
- YouTube: providers [youtube]; text = YouTube description; youtubeData {title, type "short", privacy "public", tags, category "SCIENCE_TECHNOLOGY", madeForKids false}.
- Facebook: providers [facebook]; text = Facebook caption; facebookData {type "REEL", title}.
- Instagram: providers [instagram]; text = Instagram caption; instagramData {type "REEL", showReelOnFeed true}.
Same media URL and time for all four. Use `videoCoverMilliseconds` ≈ the hook frame (e.g. 2500) for a cover where supported; omit it if Metricool rejects it. Record all 4 ids/uuids/planner links in history.

## Reporting
Never call anything published until getScheduledPosts shows status PUBLISHED with a public URL for that network.

## Content focus
Custom web development first, while still rotating WordPress, Shopify, WooCommerce and all other skills (content/topics.md).

## History of changes
- 2026-11-02: first posts under the personal "Muhammad Naveed" brand with portfolio link (2026-11-02_v1/v2). From 2026-11-03: SK Developer company brand, WhatsApp-only contact, no GitHub links, 4 platform-specific posts per video.
