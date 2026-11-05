# UPDATE 2026-11-05 — voice, visuals, daily layout, web-development focus (owner request)

Owner (in chat, 2026-11-05): "please use voice and use icon or cartoon or possible human or typing or more added, and daily layout change. Why our video not ranking… make best web development focus."
This file wins over earlier instructions where they conflict. Everything else (brand, WhatsApp-only CTA, no GitHub links, 4 platform packages, honesty rules) stays.

## 1. Voiceover — mandatory on every video
- Before rendering run `bash tools/voice/fetch_model.sh` (downloads the Piper voice + CMU dictionary into the git-ignored tools/voice/models/ via git; ~80 MB; pip/HF are blocked in the sandbox).
- Spec: `"voice": {"speaker": <id>, "speed": 1.0–1.1}`. Every scene except a silent end card has a `vo` line. Scene length follows the voice automatically.
- Speakers that sound clean: male 5, 7, 8; female 9, 14, 18. Alternate male/female between the two daily videos and across days.
- Write VO for the ear: short sentences, numbers as words ("two a.m."), brand names the lexicon knows (WordPress, Shopify, WooCommerce, WhatsApp, API, CRM, SEO, UI, UX, PHP). Check unknown-word warnings `[tts] unknown word spelled out` and rephrase or add the word to LEX in tools/voice/tts.py.
- Subtitles are burned in automatically from the VO (not on cta/endscreen unless `"captions": true`).
- If the voice model cannot be fetched, render without voice and say so in the report (never claim voice that isn't there).

## 2. Visual richness — at least TWO of these per video
- `character`: illustrated developer typing at a laptop (cartoon; never presented as a real person or as the owner). Fields: title, typed (lines that get typed), icons, pose typing|wave, skin 0–3, shirt "#hex", scale.
- `search`: a search bar that types a query, then result cards with icons. Fields: title, query, results [[title, sub, icon]], highlight, label ("Concept demo" when it looks like a real UI).
- `icons`: icon grid [[icon, label]] (2×2 or 3×2).
- Icons in `list` items `[title, sub, icon]`, `steps` items `[title, sub, icon]`, `chips` items `[label, icon]`.
- Icon names: cart, chat, calendar, chart, code, lock, rocket, phone, globe, gear, bolt, search, user, card, mail, star, clock, layout, server, wordpress, bag, speed, shield, link, bot.
- Keep the existing types (code typing, browser, dashboard, chat, compare…) in rotation.

## 3. Daily layout change
- Every spec sets `"layout": {"cards": "solid|outline|glass", "captions": "box|bar|outline", "progress": "bottom|top", "align": "left|center" (optional)}`.
- The two videos of a day use different layout combos, and neither repeats the previous day's combos. Record `layout` in history.

## 4. Hook & length (retention)
- First frame = the viewer's problem as a short question or bold claim; voice starts immediately (first scene VO ≤ 3 s).
- Something moves in the first second (kinetic words, typing, character).
- Target 22–32 s. Cut any scene that doesn't add new information.

## 5. Topic focus: web development first
- At least one video per day is core web development: business websites, WordPress (custom themes/plugins, speed, security), Shopify (themes, sections, speed), WooCommerce, custom web apps (React/Next.js/Node.js/PHP/Laravel), landing pages that convert, website speed, mobile-first/responsive UI, SEO-ready builds, website redesign, maintenance.
- The second video may use the other pillars (CRM, dashboards, booking, AI chatbots, APIs, Flutter), framed around the website/web app where natural.
- Hooks and titles use searchable phrases people actually type (e.g. "why is my website slow", "Shopify vs WooCommerce", "website cost"). Never invent prices, stats, clients or results.

## 6. Performance loop
- Each daily run also pulls Metricool analytics for the last 7 days (Instagram IGRE02/23/11/24, Facebook FBRE02/10/11/13, YouTube YTVP02/17/06/08, TikTok TKPO02/07/11/13) and appends a short table to content/growth/YYYY-MM-DD_performance.md. Note which hooks/layouts kept people watching longest and lean that way. Never promise ranking.
