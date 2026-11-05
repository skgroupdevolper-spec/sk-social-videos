# SK Developer — daily social video pipeline

Read these first, in order. Later files win over earlier ones where they conflict:
1. `content/INSTRUCTIONS.md` — original rulebook (research, uniqueness, validation, honesty rules).
2. `content/INSTRUCTIONS_UPDATE_2026-11-02.md` — **current brand and packaging rules** (SK Developer company brand, 4 platform packages, WhatsApp-only contact, no GitHub links).
2b. `content/INSTRUCTIONS_UPDATE_2026-11-05.md` — **voiceover on every video, icons/illustrated character/typing scenes, a new layout every day, web-development-first topics, daily performance check.**
3. `content/publishing.md` — platforms, slots, authorisation, how to schedule 4 platform-specific posts.
4. `content/topics.md` — skills rotation (WordPress, Shopify, WooCommerce AND custom software).
5. `content/history/history.json` — never repeat a hook, topic, title, CTA wording, scene sequence, theme+music pair or main benefit.

## Brand (from 2026-11-03 onward)
- Company: **SK Developer** — premium full-stack software development & intelligent digital solutions.
- Brand block for every spec: `{"name":"SK Developer","role":"Full-Stack Software Development","mark":"SK","phone":"+92 325 2314412"}`
- Contact: WhatsApp only — **+92 325 2314412**, link **https://wa.me/923252314412**. No other phone number. **No GitHub or GitHub Pages links** (so no portfolio URL) in videos, captions, descriptions or comments.
- Colours: white, black and orange. Themes in gen.py: `ink`, `paper`, `graphite`, `flame`, `studio`. The two videos of a day never share a theme, a music mood or a scene sequence.
- Only claim capabilities SK Developer can genuinely deliver (list in INSTRUCTIONS_UPDATE §1). Never invent clients, results, statistics, testimonials, prices or certifications. Mockups (browser, dashboard, chat) are always labelled "Concept demo".

## Renderer — `tools/gen.py`
`python3 tools/gen.py spec.json video.mp4 --preview` → contact sheet; without `--preview` → video + `thumbnail.jpg`.
Scene types: hook, kinetic, statement, stat (true numbers only), intro, list (good:false = red ✕), steps, chips, compare, code, browser, dashboard (kind admin|booking|store), chat (AI chatbot conversation), character (illustrated developer typing), search (typed search + result cards), icons (icon grid), cta, endscreen.
- Voice: run `bash tools/voice/fetch_model.sh` once per session, then add `"voice": {"speaker": 8, "speed": 1.05}` and a `vo` line per scene; subtitles are burned in automatically. `python3 tools/voice/tts.py "text" out.wav --speaker 8` to test a line.
- Layout: `"layout": {"cards": "solid|outline|glass", "captions": "box|bar|outline", "progress": "bottom|top"}` — change it every day.
- Icons: list/steps items `[title, sub, icon]`, chips items `[label, icon]`; names in tools/art.py ICONS.
- `cta`: `kicker` (small caps line, e.g. "Have a project in mind?"), `lines` (headline, last line orange), `sub`, `button` (label above the number), `link` + `link_label` (use `"wa.me/923252314412"` / `"WhatsApp"`). Never set `portfolio`.
- `endscreen`: branded end card — SK mark, company name, `tagline`, green `button` (e.g. "Discuss your project on WhatsApp"), number and wa.me link. Use it as the last scene when the CTA scene alone isn't enough.
- Safe area: key text stays between y 220 and 1560 and clear of the right 130 px (TikTok/Reels/Shorts buttons). The renderer already keeps cards inside this; keep headlines short.
- Vary CTA wording every video (see INSTRUCTIONS_UPDATE §5 for examples; write new ones too). The in-video button is a visual CTA, not clickable — never describe it as clickable.

## Output per video — `exports/YYYY-MM-DD_v1|v2/`
`spec.json`, `video.mp4`, `thumbnail.jpg` (cover), `package.md` built from `content/templates/package_template.md` with **four separate platform packages** (TikTok, YouTube Shorts, Facebook Reels, Instagram Reels), each with its own title, opening text, caption/description, CTA wording, hashtags, keywords and pinned-comment suggestion, plus a production status table. Do not copy one caption to all platforms.

## Daily run
1. Read the files above. 2. Update statuses of earlier posts from Metricool, and pull 7-day analytics into content/growth/ (INSTRUCTIONS_UPDATE_2026-11-05 §6). 3. Keyword research with WebSearch/WebFetch (record sources, mark volume as unverified). 4. Plan 2 different videos (see topics.md). 5. Specs → preview once → fix overflow → render. 6. Validate (1080×1920, 30 fps, 22–45 s, voice + music audio, subtitles readable, spelling). 7. package.md with 4 platform packages. 8. Update history (append; never overwrite past entries). 9. Commit and push. 10. Schedule 4 platform-specific Metricool posts per video (publishing.md). 11. Report with the status ladder: created → packages prepared → uploaded/scheduled → published (published only when Metricool shows PUBLISHED with a public URL).

## Metricool
Brand blogId 7815878, timezone America/Los_Angeles. Media URL for a pushed video:
`https://raw.githubusercontent.com/skgroupdevolper-spec/sk-social-videos/main/exports/<id>/video.mp4`
(This raw URL is only a file host for Metricool. Never show it, or any GitHub link, to viewers.)
