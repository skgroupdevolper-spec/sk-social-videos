# Muhammad Naveed — daily social video pipeline

Read `content/INSTRUCTIONS.md` first: it is the owner's rulebook and wins over anything here.

## Layout
- `tools/gen.py` — renders a 1080×1920 MP4 (with an original procedural music track) from a JSON spec. `python3 tools/gen.py spec.json out.mp4 --preview` writes a contact sheet; without `--preview` it renders the video and `thumbnail.jpg`.
- `content/history/history.json` — every video made: topic, hook, keywords, design, scenes, music, CTA, status, links. Check it before planning; never repeat a hook, topic, title, CTA wording, scene sequence, theme+music pair or main benefit.
- `content/research/YYYY-MM-DD.md` — keyword research notes with sources and limitations.
- `exports/YYYY-MM-DD_v1|v2/` — `spec.json`, `video.mp4`, `thumbnail.jpg`, `package.md` (title, keywords, script table, caption, description, CTA, posting time, research summary and sources).

## Brand
White, black and orange. Themes in gen.py: `ink`, `paper`, `graphite`, `flame`, `studio`. The two videos of a day never share a theme, a music mood or a scene sequence.
Scene types: hook, kinetic, statement, stat (true numbers only), intro, list (good:false = red ✕), steps, chips, compare, code, browser (label "Concept demo"), cta (WhatsApp + portfolio).
Brand block: {"name":"Muhammad Naveed","role":"WordPress · Shopify · Full-Stack Developer","mark":"MN","phone":"+92 325 2314412"}
Portfolio: naveed786-king.github.io/Naveedsoft.com · WhatsApp link: https://wa.me/923252314412

## Daily run
1. Read history. 2. Keyword research with WebSearch/WebFetch (record sources, mark volume as unverified). 3. Video 1 = authority/educational, Video 2 = career branding (occasionally client-focused). 4. Write specs, preview once, fix overflow, render. 5. Validate (resolution, duration 25–45 s, audio present, spelling). 6. Write package.md. 7. Update history. 8. Commit and push. 9. Publish only as the owner authorised (see `content/publishing.md`).

## Metricool
Brand blogId 7815878, timezone America/Los_Angeles. Media URL for a pushed video:
`https://raw.githubusercontent.com/skgroupdevolper-spec/sk-social-videos/main/exports/<id>/video.mp4`
