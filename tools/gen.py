#!/usr/bin/env python3
"""Sk Developer social video generator.

Usage:
  python3 gen.py spec.json out.mp4            # full render (video + music)
  python3 gen.py spec.json out.mp4 --preview  # contact sheet only (out_preview.jpg)

The spec picks a visual theme, a music mood/seed and a list of scenes.
See topics.md for the spec format and the content plan.
"""
import sys, os, json, math, subprocess, tempfile, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art

W, H, FPS = 1080, 1920, 30
MIN_TOTAL = 32.0
SAFE_R = 130   # right margin kept clear of TikTok/Instagram/Reels action buttons
SAFE_TOP, SAFE_BOTTOM = 220, 1560   # key text stays inside this band on all 4 platforms
FD = "/usr/share/fonts/opentype/inter/"
def _f(name, fallback):
    p = FD + name
    return p if os.path.exists(p) else fallback
DJ = "/usr/share/fonts/truetype/dejavu/"
F = {
    "black": _f("InterDisplay-Black.otf", DJ + "DejaVuSans-Bold.ttf"),
    "xb": _f("InterDisplay-ExtraBold.otf", DJ + "DejaVuSans-Bold.ttf"),
    "bold": _f("InterDisplay-Bold.otf", DJ + "DejaVuSans-Bold.ttf"),
    "semi": _f("Inter-SemiBold.otf", DJ + "DejaVuSans-Bold.ttf"),
    "med": _f("Inter-Medium.otf", DJ + "DejaVuSans.ttf"),
    "reg": _f("Inter-Regular.otf", DJ + "DejaVuSans.ttf"),
    "mono": DJ + "DejaVuSansMono-Bold.ttf",
    "serif": DJ + "DejaVuSerif-Bold.ttf",
}

def hexc(s): s = s.lstrip("#"); return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))

# ------------------------------------------------------------------ themes
THEMES = {
    # Brand family: white, black and orange. Each theme also changes layout, motion and texture.
    "ink": dict(bg=["#0B0B0C", "#151517"], text="#FFFFFF", muted="#A3A3A8", accent="#FF6A1A", accent2="#FFFFFF",
                card="#18181B", border="#2A2A2E", motif="grid", align="left", head="black", enter="up",
                exit="slide", radius=22, glow=["#FF6A1A", "#3A1A08"]),
    "paper": dict(bg=["#FFFFFF", "#F4F4F2"], text="#0B0B0C", muted="#5E5E66", accent="#F25C05", accent2="#0B0B0C",
                  card="#F3F3F1", border="#E2E2DF", motif="lines", align="left", head="black", enter="left",
                  exit="fade", radius=16, glow=None),
    "graphite": dict(bg=["#1A1B1E", "#232428"], text="#FFFFFF", muted="#B0B0B6", accent="#FF7A2F", accent2="#FFD2B3",
                     card="#2A2B30", border="#3A3B41", motif="dots", align="center", head="xb", enter="scale",
                     exit="fade", radius=32, glow=["#FF7A2F", "#6B6B70"]),
    "flame": dict(bg=["#FF5A0A", "#E84300"], text="#FFFFFF", muted="#FFE3D1", accent="#111111", accent2="#FFFFFF",
                  card="#D63F00", border="#FF8A4D", motif="diagonal", align="center", head="black", enter="up",
                  exit="slide", radius=40, glow=None),
    "studio": dict(bg=["#F6F6F4", "#EDEDEA"], text="#111111", muted="#64646B", accent="#FF5F00", accent2="#111111",
                   card="#FFFFFF", border="#DADAD6", motif="circles", align="center", head="xb", enter="scale",
                   exit="slide", radius=28, glow=None),
}

_fc = {}
def font(k, s):
    s = max(8, int(round(s)))
    key = (k, s)
    if key not in _fc: _fc[key] = ImageFont.truetype(F[k], s)
    return _fc[key]

def clamp(x): return max(0.0, min(1.0, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def back(x):
    x = clamp(x); c = 1.5
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def A(c, a): return tuple(c) + (int(255 * clamp(a)),)
_tmp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
def tw(s, f): return _tmp.textlength(s, font=f)

def wrap(text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if tw(t, f) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

VO_LEAD = 0.3   # seconds of silence before each scene's voiceover starts

def caption_chunks(text, dur, lead):
    """Split voiceover text into short subtitle chunks, timed by character count across the voice length."""
    words = text.replace("—", ",").split()
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 5 or len(" ".join(cur)) > 26 or w[-1] in ".,?!:;":
            chunks.append(" ".join(cur)); cur = []
    if cur: chunks.append(" ".join(cur))
    tot = sum(len(c) + 3 for c in chunks) or 1
    out, t0 = [], lead
    for c in chunks:
        d = dur * (len(c) + 3) / tot
        out.append((t0, t0 + d, c.rstrip(",;:"))); t0 += d
    return out

def fit_size(lines, k, maxw, maxs, mins=40):
    s = maxs
    while s > mins and max(tw(l, font(k, s)) for l in lines) > maxw: s -= 4
    return s

# ------------------------------------------------------------------ renderer
class R:
    def __init__(self, spec):
        self.spec = spec
        th = dict(THEMES[spec.get("theme", "midnight")])
        for k in ("text", "muted", "accent", "accent2", "card", "border"): th[k] = hexc(th[k])
        th["bg_c"] = hexc(th["bg"][0])
        self.th = th
        self.brand = spec.get("brand", {})
        self.lay = spec.get("layout", {})
        if self.lay.get("align"): th["align"] = self.lay["align"]
        self.left = th["align"] == "left"
        self.X = 90 if self.left else None
        self.base = self.make_base()
        self.blobs = [self.make_blob(hexc(c), r) for c, r in zip(th["glow"], (380, 300))] if th["glow"] else []
        self.light = sum(hexc(th["bg"][0])) > 600
        self.scenes = spec["scenes"]
        self.vo, self.vsr, self.caps = [None] * len(self.scenes), 22050, [[] for _ in self.scenes]
        vc = spec.get("voice")
        if vc:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice"))
            import tts
            v = tts.Voice(); self.vsr = v.sr
            for i, sc in enumerate(self.scenes):
                if sc.get("vo"):
                    self.vo[i] = v.say(sc["vo"], int(vc.get("speaker", 0)), float(vc.get("speed", 1.0)))
                    self.caps[i] = caption_chunks(sc["vo"], len(self.vo[i]) / self.vsr, VO_LEAD if i else 0.15)
        self.durs = [self.scene_dur(s) for s in self.scenes]
        if vc:
            for i, a in enumerate(self.vo):
                if a is not None:
                    self.durs[i] = max(2.4, len(a) / self.vsr + (VO_LEAD if i else 0.15) + float(self.scenes[i].get("tail", .45)))
            if sum(self.durs) < 25: self.durs[-1] += 25 - sum(self.durs)
        tot = sum(self.durs)
        if tot < MIN_TOTAL and not vc:
            k = MIN_TOTAL / tot
            self.durs = [d * k for d in self.durs]
        self.total = sum(self.durs)
        self.starts = [sum(self.durs[:i]) for i in range(len(self.durs))]

    def scene_dur(self, s):
        t = s["type"]
        n = len(s.get("items", []))
        base = {"hook": 4.6, "statement": 4.4, "stat": 4.4, "list": 2.4 + 1.0 * n, "steps": 2.6 + 1.0 * n,
                "chips": 4.4, "compare": 6.4, "intro": 4.8, "cta": 6.4,
                "kinetic": 1.6 + .42 * len(s.get("words", [])) + (1.2 if s.get("sub") else 0),
                "code": 2.6 + s.get("type_time", 3.2) + (1.2 if s.get("caption") else 0),
                "browser": 2.4 + .45 * len(s.get("callouts", [])),
                "endscreen": 4.2, "chat": 1.8 + .9 * len(s.get("messages", [])) + (1.0 if s.get("caption") else 0),
                "dashboard": 2.6 + .45 * len(s.get("callouts", [])),
                "character": 5.0, "search": 3.0 + .06 * len(s.get("query", "")) + .5 * len(s.get("results", [])),
                "icons": 2.4 + .35 * len(s.get("items", []))}.get(t, 4.5)
        return float(s.get("dur", base))

    def make_base(self):
        th = self.th
        c1, c2 = hexc(th["bg"][0]), hexc(th["bg"][1])
        g = np.linspace(0, 1, H)[:, None]
        arr = (np.array(c1)[None, None, :] * (1 - g[..., None]) + np.array(c2)[None, None, :] * g[..., None])
        arr = np.repeat(arr, W, axis=1).astype(np.uint8)
        img = Image.fromarray(arr, "RGB").convert("RGBA")
        d = ImageDraw.Draw(img)
        light = sum(c1) > 600
        acc = th["accent"]
        mc = tuple(int(c1[i] * 0.9 + acc[i] * 0.1) for i in range(3)) if light else tuple(min(255, int(v + 26)) for v in c1)
        m = th["motif"]
        if m == "dots":
            for y in range(40, H, 60):
                for x in range(40, W, 60): d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=mc + (255,))
        elif m == "grid":
            for x in range(0, W, 90): d.line([(x, 0), (x, H)], fill=mc + (255,), width=1)
            for y in range(0, H, 90): d.line([(0, y), (W, y)], fill=mc + (255,), width=1)
        elif m == "diagonal":
            for x in range(-H, W, 70): d.line([(x, 0), (x + H, H)], fill=mc + (255,), width=2)
        elif m == "lines":
            for y in range(0, H, 48): d.line([(0, y), (W, y)], fill=mc + (255,), width=1)
            d.rectangle([0, 0, 18, H], fill=th["accent"] + (255,))
        elif m == "circles":
            for (cx, cy, r) in [(W + 80, 300, 360), (-120, 1500, 420), (W - 100, 1750, 200)]:
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=mc + (255,))
        elif m == "rings":
            for r in range(200, 1600, 140):
                d.ellipse([W / 2 - r, 900 - r, W / 2 + r, 900 + r], outline=mc + (255,), width=2)
        return img

    def make_blob(self, col, r):
        s = r * 3
        b = Image.new("RGBA", (s, s), col + (0,))
        m = Image.new("L", (s, s), 0)
        ImageDraw.Draw(m).ellipse([r, r, 2 * r, 2 * r], fill=110)
        b.putalpha(m.filter(ImageFilter.GaussianBlur(r / 2.2)))
        return b

    def background(self, gt):
        img = self.base.copy()
        if self.blobs:
            img.alpha_composite(self.blobs[0], (int(-300 + 160 * math.sin(gt * .25)), int(200 + 140 * math.cos(gt * .2))))
            img.alpha_composite(self.blobs[1], (int(380 + 140 * math.cos(gt * .22)), int(1100 + 160 * math.sin(gt * .18))))
        return img

    # ---- primitives
    def txt(self, d, x, y, s, f, col, a):
        if a <= 0: return
        if x is None: x = (W - tw(s, f)) / 2
        d.text((x, y), s, font=f, fill=A(col, a))

    def enter(self, t, start, dur=0.55):
        k = ease((t - start) / dur)
        e = self.th["enter"]
        if e == "left": return k, -60 * (1 - k), 0
        if e == "scale": return k, 0, 30 * (1 - k)
        return k, 0, 50 * (1 - k)

    def line(self, d, t, start, y, s, f, col):
        k, dx, dy = self.enter(t, start)
        if k <= 0: return
        x = self.X + dx if self.left else (W - tw(s, f)) / 2 + dx
        d.text((x, y + dy), s, font=f, fill=A(col, k))

    def block(self, d, t, start, y, text, k_font, size, col, maxw=None, gap=1.12, step=0.12):
        maxw = maxw or (W - 180)
        lines = wrap(text, font(k_font, size), maxw)
        for i, l in enumerate(lines):
            self.line(d, t, start + i * step, y + i * size * gap, l, font(k_font, size), col)
        return y + len(lines) * size * gap

    def headline(self, d, t, start, y, lines, accent_idx=(), maxs=130):
        th = self.th
        s = fit_size(lines, th["head"], W - 180, maxs)
        for i, l in enumerate(lines):
            col = th["accent"] if i in accent_idx else th["text"]
            self.line(d, t, start + i * 0.16, y + i * s * 1.08, l, font(th["head"], s), col)
        return y + len(lines) * s * 1.08

    def card(self, d, x0, y0, x1, y1, a, active=False):
        th = self.th
        st = self.lay.get("cards", "solid")
        if st == "outline":
            d.rounded_rectangle([x0, y0, x1, y1], radius=th["radius"], outline=A(th["accent"] if active else th["muted"], a), width=4 if active else 3)
            return
        if st == "glass":
            d.rounded_rectangle([x0 + 10, y0 + 14, x1 + 10, y1 + 14], radius=th["radius"], fill=A((0, 0, 0), .10 * a))
            d.rounded_rectangle([x0, y0, x1, y1], radius=th["radius"], fill=A(th["card"], .92 * a),
                                outline=A(th["accent"] if active else th["border"], a), width=4 if active else 2)
            d.rounded_rectangle([x0, y0, x0 + 14, y1], radius=7, fill=A(th["accent"], a))
            return
        d.rounded_rectangle([x0, y0, x1, y1], radius=th["radius"], fill=A(th["card"], a),
                            outline=A(th["accent"] if active else th["border"], a), width=4 if active else 2)

    def badge(self, d, cx, cy, r, label, a, col=None, fg=None):
        th = self.th
        col = col or th["accent"]
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=A(col, a))
        f = font("black", r * 0.95)
        bb = d.textbbox((0, 0), label, font=f)
        fg = fg or ((255, 255, 255) if sum(col) < 520 else (12, 12, 20))
        d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), label, font=f, fill=A(fg, a))

    def check(self, d, cx, cy, r, a, k, good=True):
        th = self.th
        col = th["accent2"] if good else (235, 87, 87)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=A(col, a))
        fg = (255, 255, 255) if not good or sum(col) < 450 else (10, 14, 24)
        w = int(r * 0.24)
        if good:
            p1, p2, p3 = (cx - r * .45, cy + r * .02), (cx - r * .1, cy + r * .38), (cx + r * .5, cy - r * .35)
            if k > 0: d.line([p1, p2], fill=A(fg, a), width=w)
            if k > .5:
                kk = (k - .5) * 2
                d.line([p2, (p2[0] + (p3[0] - p2[0]) * kk, p2[1] + (p3[1] - p2[1]) * kk)], fill=A(fg, a), width=w)
        elif k > 0:
            q = r * 0.38 * min(1, k * 1.5)
            d.line([(cx - q, cy - q), (cx + q, cy + q)], fill=A(fg, a), width=w)
            d.line([(cx - q, cy + q), (cx + q, cy - q)], fill=A(fg, a), width=w)

    def pill(self, d, x, cy, s, f, fg, bg, a, outline=None, h=72):
        w = tw(s, f) + 68
        if x is None: x = (W - w) / 2
        d.rounded_rectangle([x, cy - h / 2, x + w, cy + h / 2], radius=h / 2, fill=A(bg, a) if bg else None,
                            outline=A(outline, a) if outline else None, width=3)
        bb = d.textbbox((0, 0), s, font=f)
        d.text((x + w / 2 - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), s, font=f, fill=A(fg, a))
        return w

    # ---- chrome
    def header(self, d, gt):
        th = self.th; k = ease(gt / .8)
        x, y = 70, 110
        d.rounded_rectangle([x, y, x + 92, y + 92], radius=min(26, th["radius"]), fill=A(th["accent"], k))
        f = font("bold", 40); s = self.brand.get("mark", "SK")
        bb = d.textbbox((0, 0), s, font=f)
        fg = (255, 255, 255) if sum(th["accent"]) < 520 else (12, 12, 20)
        d.text((x + 46 - (bb[2] - bb[0]) / 2 - bb[0], y + 46 - (bb[3] - bb[1]) / 2 - bb[1]), s, font=f, fill=A(fg, k))
        d.text((x + 116, y + 6), self.brand.get("name", "SK Developer"), font=font("bold", 44), fill=A(th["text"], k))
        d.text((x + 116, y + 58), self.brand.get("role", "Full-Stack Software Development"), font=font("med", 28), fill=A(th["muted"], k))

    def progress(self, d, gt):
        th = self.th; y = 52 if self.lay.get("progress") == "top" else H - 90
        d.rounded_rectangle([70, y, W - 70, y + 8], radius=4, fill=A(th["border"], 1))
        d.rounded_rectangle([70, y, 70 + (W - 140) * clamp(gt / self.total), y + 8], radius=4, fill=A(th["accent"], 1))

    # ---- scenes
    def s_hook(self, d, t, s):
        th = self.th; y = 600
        if s.get("label"):
            f = font("semi", 32)
            k = ease(t / .5)
            self.pill(d, self.X, y, s["label"].upper(), f, th["accent2"], None, k, outline=th["accent2"])
            y += 90
        lines = s["lines"] + ([s["accent_line"]] if s.get("accent_line") else [])
        acc = (len(lines) - 1,) if s.get("accent_line") else ()
        y = self.headline(d, t, .25, y, lines, acc, maxs=132)
        k2 = ease((t - 1.0) / .7)
        if k2 > 0:
            x0 = self.X if self.left else W / 2 - 300
            d.rounded_rectangle([x0, y + 20, x0 + 600 * k2, y + 30], radius=5, fill=A(th["accent2"], 1))
        if s.get("sub"): self.block(d, t, 1.4, y + 70, s["sub"], "med", 50, th["muted"])

    def s_statement(self, d, t, s):
        th = self.th
        y = 620
        if s.get("label"):
            self.line(d, t, 0, y, s["label"].upper(), font("semi", 34), th["accent2"]); y += 80
        y = self.headline(d, t, .2, y, s["lines"], tuple(s.get("accent", [len(s["lines"]) - 1])), maxs=118)
        if s.get("sub"): self.block(d, t, 1.2, y + 50, s["sub"], "med", 48, th["muted"])

    def s_stat(self, d, t, s):
        th = self.th
        sc = back(t / .6)
        if sc > .02:
            f = font("black", 300 * sc)
            big = s["big"]
            if self.left: x = 90
            else: x = (W - tw(big, f)) / 2
            bb = d.textbbox((0, 0), big, font=f)
            d.text((x, 720 - (bb[3] - bb[1]) / 2 - bb[1]), big, font=f, fill=A(th["accent"], 1))
        y = self.block(d, t, .6, 930, s["text"], "bold", 66, th["text"])
        if s.get("sub"): self.block(d, t, 1.1, y + 30, s["sub"], "med", 44, th["muted"])

    def s_intro(self, d, t, s):
        th = self.th
        cx = 90 + 150 if self.left else W / 2; cy = 640
        k = back(t / .7); r = 150 * k
        if r > 2:
            for i, rr in enumerate([r + 34, r + 18]):
                d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=A(th["accent"] if i else th["accent2"], .6), width=4)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=A(th["card"], 1))
            f = font("black", 120 * k); ini = s.get("initials", "SK")
            bb = d.textbbox((0, 0), ini, font=f)
            d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), ini, font=f, fill=A(th["text"], 1))
        y = self.headline(d, t, .4, 860, [s["title"]], (), maxs=84)
        y = self.block(d, t, .6, y + 20, s.get("sub", ""), "med", 48, th["muted"])
        for i, (big, small) in enumerate(s.get("stats", [])[:2]):
            kk = ease((t - 1.1 - i * .2) / .55)
            if kk <= 0: continue
            x0 = 90 + i * 470; y0 = y + 60 + 40 * (1 - kk)
            self.card(d, x0, y0, x0 + 430, y0 + 230, kk)
            d.text((x0 + 40, y0 + 34), big, font=font("black", 88), fill=A(th["accent"] if i == 0 else th["accent2"], kk))
            d.text((x0 + 42, y0 + 150), small, font=font("med", 34), fill=A(th["muted"], kk))

    def s_list(self, d, t, s):
        th = self.th
        items = s["items"]; n = len(items)
        y = self.headline(d, t, 0, 520 - 70 * max(0, n - 3), wrap(s["title"], font(th["head"], 84), W - 180), (), maxs=84)
        ch = 185 if n <= 4 else 160; gap = 30 if n <= 4 else 22
        y0s = y + 50
        good = s.get("good", True); numbered = s.get("numbered", False)
        for i, it in enumerate(items):
            a_, b_ = (it + [""])[:2] if isinstance(it, list) else (it, "")
            st = .5 + i * .38
            kk = ease((t - st) / .5)
            if kk <= 0: continue
            yy = y0s + i * (ch + gap) + 40 * (1 - kk)
            self.card(d, 90, yy, W - SAFE_R, yy + ch, kk)
            ic = it[2] if isinstance(it, list) and len(it) > 2 else None
            if ic:
                d.ellipse([180 - 50, yy + ch / 2 - 50, 180 + 50, yy + ch / 2 + 50], fill=A(th["accent"], kk))
                art.icon(d, ic, 180, yy + ch / 2, 54, (255, 255, 255) if sum(th["accent"]) < 520 else (12, 12, 20), kk)
            elif numbered: self.badge(d, 180, yy + ch / 2, 44, str(i + 1), kk)
            else: self.check(d, 180, yy + ch / 2, 44, kk, ease((t - st - .15) / .4), good)
            ff = font("bold", 50)
            if b_:
                d.text((260, yy + ch / 2 - 66), a_, font=ff, fill=A(th["text"], kk))
                sub = wrap(b_, font("reg", 36), W - 400)[0]
                d.text((260, yy + ch / 2 + 6), sub, font=font("reg", 36), fill=A(th["muted"], kk))
            else:
                bb = d.textbbox((0, 0), a_, font=ff)
                d.text((260, yy + ch / 2 - (bb[3] - bb[1]) / 2 - bb[1]), a_, font=ff, fill=A(th["text"], kk))

    def s_steps(self, d, t, s):
        th = self.th
        y = self.headline(d, t, 0, 400, [s["title"]], (), maxs=88)
        if s.get("sub"): y = self.block(d, t, .2, y + 10, s["sub"], "med", 44, th["muted"])
        items = s["items"]; x = 200; y0 = y + 150; step = min(320, 1050 / len(items))
        kl = ease((t - .6) / 2.0)
        d.rounded_rectangle([x - 4, y0, x + 4, y0 + step * (len(items) - 1) * kl], radius=4, fill=A(th["border"], 1))
        for i, it in enumerate(items):
            a_, b_ = (it + [""])[:2]
            ic = it[2] if len(it) > 2 else None
            st = .5 + i * .6
            kk = back((t - st) / .5); yy = y0 + i * step
            if kk > .02:
                last = i == len(items) - 1
                col = th["accent2"] if last else th["accent"]
                if ic:
                    d.ellipse([x - 68 * kk, yy - 68 * kk, x + 68 * kk, yy + 68 * kk], fill=A(col, 1))
                    art.icon(d, ic, x, yy, 70 * kk, (255, 255, 255) if sum(col) < 520 else (12, 12, 20), 1)
                else: self.badge(d, x, yy, 68 * kk, str(i + 1), 1, col=col)
            k2 = ease((t - st - .1) / .5)
            if k2 > 0:
                d.text((320 + 40 * (1 - k2), yy - 62), a_, font=font("bold", 52), fill=A(th["text"], k2))
                d.text((320 + 40 * (1 - k2), yy + 10), wrap(b_, font("reg", 38), W - 420)[0] if b_ else "",
                       font=font("reg", 38), fill=A(th["muted"], k2))

    def s_chips(self, d, t, s):
        th = self.th
        y = self.headline(d, t, 0, 580, [s["title"]], (), maxs=84)
        if s.get("sub"): y = self.block(d, t, .2, y + 10, s["sub"], "med", 42, th["muted"])
        f = font("semi", 46)
        rows, cur, curw = [], [], 0
        icons = {}
        items = []
        for it in s["items"]:
            if isinstance(it, list): icons[it[0]] = it[1]; it = it[0]
            items.append(it)
        for it in items:
            w = tw(it, f) + 80 + (62 if it in icons else 0)
            if cur and curw + w + 28 > W - 160: rows.append(cur); cur, curw = [], 0
            cur.append(it); curw += w + 28
        if cur: rows.append(cur)
        idx = 0; cols = [th["accent"], th["accent2"], th["text"]]
        for r, row in enumerate(rows):
            widths = [tw(x, f) + 80 + (62 if x in icons else 0) for x in row]
            total = sum(widths) + 28 * (len(row) - 1)
            x = 90 if self.left else (W - total) / 2
            cy = y + 110 + r * 140
            for it, w in zip(row, widths):
                kk = back((t - .45 - idx * .09) / .45)
                if kk > .02:
                    cw, chh = w * kk, 100 * kk; xc = x + w / 2
                    d.rounded_rectangle([xc - cw / 2, cy - chh / 2, xc + cw / 2, cy + chh / 2], radius=chh / 2,
                                        fill=A(th["card"], 1), outline=A(cols[idx % 3], 1), width=4)
                    ff = font("semi", 46 * kk); bb = d.textbbox((0, 0), it, font=ff)
                    off = 31 * kk if it in icons else 0
                    if it in icons: art.icon(d, icons[it], xc - cw / 2 + 52 * kk, cy, 44 * kk, cols[idx % 3], 1)
                    d.text((xc - (bb[2] - bb[0]) / 2 - bb[0] + off, cy - (bb[3] - bb[1]) / 2 - bb[1]), it, font=ff, fill=A(th["text"], 1))
                x += w + 28; idx += 1

    def s_compare(self, d, t, s):
        th = self.th
        y = self.headline(d, t, 0, 470, wrap(s["title"], font(th["head"], 80), W - 180), (), maxs=80)
        cols = [(s["left"], False), (s["right"], True)]
        nmax = max(len(s["left"]["items"][:5]), len(s["right"]["items"][:5]))
        chh = 190 + nmax * 150
        cw = (W - 90 - SAFE_R - 30) / 2
        for c, (side, good) in enumerate(cols):
            st = .4 + c * 1.6
            k = ease((t - st) / .5)
            if k <= 0: continue
            x0 = 90 + c * (cw + 30); y0 = y + 60 + 40 * (1 - k)
            self.card(d, x0, y0, x0 + cw, y0 + chh, k, active=good)
            lab = side["label"]
            d.text((x0 + 36, y0 + 36), lab, font=font("xb", 54), fill=A(th["accent2"] if good else th["muted"], k))
            for i, it in enumerate(side["items"][:5]):
                ki = ease((t - st - .3 - i * .22) / .4)
                if ki <= 0: continue
                yy = y0 + 160 + i * 150
                self.check(d, x0 + 66, yy + 30, 30, ki, 1, good)
                lines = wrap(it, font("semi", 38), cw - 140)[:2]
                for j, l in enumerate(lines):
                    d.text((x0 + 116, yy + j * 46 + (0 if len(lines) > 1 else 10)), l, font=font("semi", 38), fill=A(th["text"], ki))

    def s_cta(self, d, t, s):
        th = self.th
        y0 = 420
        if s.get("kicker"):
            self.line(d, t, 0, 360, s["kicker"].upper(), font("semi", 34), th["accent"]); y0 = 430
        y = self.headline(d, t, .1, y0, s.get("lines", ["Let's build", "your website"]), tuple(s.get("accent", [len(s.get("lines", [0, 0])) - 1])), maxs=124)
        if s.get("sub"): y = self.block(d, t, .5, y + 30, s["sub"], "med", 46, th["muted"])
        green = (37, 211, 102)
        kb = back((t - .9) / .6); cy = y + 230
        if kb > .02:
            sc = kb * (1 + .03 * math.sin(max(0, t - 1.5) * 5))
            bw, bh = 900 * sc, 250 * sc
            for g in range(3):
                gg = (3 - g) * 14 * sc
                d.rounded_rectangle([W / 2 - bw / 2 - gg, cy - bh / 2 - gg, W / 2 + bw / 2 + gg, cy + bh / 2 + gg],
                                    radius=bh / 2 + gg, fill=A(green, .08))
            d.rounded_rectangle([W / 2 - bw / 2, cy - bh / 2, W / 2 + bw / 2, cy + bh / 2], radius=bh / 2, fill=A(green, 1))
            r = 72 * sc; ix = W / 2 - bw / 2 + 36 * sc + r
            d.ellipse([ix - r, cy - r, ix + r, cy + r], fill=(255, 255, 255, 255))
            br = r * .5
            d.ellipse([ix - br, cy - br, ix + br, cy + br], outline=A(green, 1), width=max(2, int(9 * sc)))
            d.polygon([(ix - br * .9, cy + br * .5), (ix - br * 1.25, cy + br * 1.25), (ix - br * .35, cy + br * .9)], fill=A(green, 1))
            tx = ix + r + 34 * sc
            d.text((tx, cy - 88 * sc), s.get("button", "WhatsApp me"), font=font("semi", 46 * sc), fill=(255, 255, 255, 255))
            d.text((tx, cy - 22 * sc), self.brand.get("phone", "+92 325 2314412"), font=font("black", 70 * sc), fill=(8, 40, 22, 255))
        k3 = ease((t - 1.6) / .5)
        if k3 > 0 and s.get("pill"):
            self.pill(d, None, cy + 240, s["pill"], font("semi", 38), th["text"], th["card"], k3, h=78)
        link = s.get("link") or s.get("portfolio")
        if k3 > 0 and link:
            lab = s.get("link_label", "Portfolio" if s.get("portfolio") else "")
            base = cy + (300 if s.get("pill") else 220)
            if lab: self.txt(d, None, base, lab, font("semi", 30), th["muted"], k3)
            self.txt(d, None, base + 42, link, font("bold", 40), th["text"], k3)
        if s.get("footer"):
            fy = cy + (330 if not (s.get("pill") and (s.get("link") or s.get("portfolio"))) else 430)
            for i, l in enumerate(s["footer"][:2]):
                k4 = ease((t - 1.9 - i * .2) / .5)
                f = font("semi" if i else "med", 40)
                self.txt(d, None, fy + i * 66, l, f, th["accent2"] if i else th["muted"], k4)


    def s_kinetic(self, d, t, s):
        """Kinetic typography: words punch in one at a time and stack."""
        th = self.th
        words = s["words"]; acc = set(s.get("accent", []))
        size = s.get("size", 150)
        lines, cur = [], []
        f = font(th["head"], size)
        for i, w in enumerate(words):
            trial = " ".join(x for _, x in cur + [(i, w)])
            if cur and tw(trial, f) > W - 180: lines.append(cur); cur = []
            cur.append((i, w))
        if cur: lines.append(cur)
        total_h = len(lines) * size * 1.05
        y0 = max(420, 900 - total_h / 2)
        step = s.get("step", 0.42)
        for li, ln in enumerate(lines):
            lw = tw(" ".join(w for _, w in ln), f)
            x = 90 if self.left else (W - lw) / 2
            for i, w in ln:
                k = clamp((t - .15 - i * step) / .28)
                if k > 0:
                    sc = 1 + .35 * (1 - ease(k))
                    ff = font(th["head"], size * sc)
                    ww = tw(w, ff); base_w = tw(w, f)
                    col = th["accent"] if i in acc else th["text"]
                    d.text((x - (ww - base_w) / 2, y0 + li * size * 1.05 - (size * sc - size) / 2), w, font=ff, fill=A(col, ease(k)))
                x += tw(w + " ", f)
        if s.get("sub"):
            st = .15 + len(words) * step + .2
            self.block(d, t, st, y0 + total_h + 40, s["sub"], "med", 48, th["muted"])

    def s_code(self, d, t, s):
        """Animated code editor with typing."""
        th = self.th
        y = self.headline(d, t, 0, 330, wrap(s["title"], font(th["head"], 76), W - 180), (), maxs=76)
        x0, y0, w = 70, y + 40, W - 140
        lines = s["lines"]
        maxlen = max(len(l) for l in lines)
        fs = max(24, min(40, int((w - 140) / (maxlen * 0.61))))
        lh = int(fs * 1.6)
        h = 110 + lh * len(lines) + 40
        k = ease((t - .2) / .5)
        if k <= 0: return
        y0 += 40 * (1 - k)
        dark = (17, 18, 22)
        d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=22, fill=A(dark, k), outline=A((48, 50, 58), k), width=2)
        for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
            d.ellipse([x0 + 28 + i * 32, y0 + 26, x0 + 48 + i * 32, y0 + 46], fill=A(c, k))
        d.text((x0 + 150, y0 + 22), s.get("file", "index.js"), font=font("mono", 26), fill=A((150, 152, 162), k))
        total = sum(len(l) for l in lines)
        typed = int(total * clamp((t - .6) / max(1.0, s.get("type_time", 3.2))))
        kw = set(s.get("keywords", ["const", "let", "function", "return", "await", "async", "import", "from", "if", "else", "export", "<img", "loading="]))
        fm = font("mono", fs)
        cy = y0 + 90; shown = 0
        for li, line in enumerate(lines):
            d.text((x0 + 22, cy), f"{li + 1:>2}", font=fm, fill=A((90, 92, 102), k))
            n = max(0, min(len(line), typed - shown)); shown += len(line)
            part = line[:n]
            # simple colouring: comments grey, strings light orange, keywords orange
            x = x0 + 100
            if part.strip().startswith("//") or part.strip().startswith("#"):
                d.text((x, cy), part, font=fm, fill=A((120, 124, 136), k))
            else:
                import re
                for tok in re.split(r"(\s+|\"[^\"]*\"?|'[^']*'?)", part):
                    if not tok: continue
                    col = (232, 234, 240)
                    if tok.startswith(("'", '"')): col = (255, 190, 140)
                    elif tok in kw or tok.rstrip("(") in kw: col = th["accent"] if sum(th["accent"]) > 200 else (255, 122, 47)
                    d.text((x, cy), tok, font=fm, fill=A(col, k)); x += tw(tok, fm)
            if 0 < n < len(line) or (n == len(line) and shown == typed and int(t * 3) % 2 == 0):
                cx = x0 + 100 + tw(part, fm)
                d.rectangle([cx + 2, cy + 4, cx + 6, cy + fs + 6], fill=A((255, 122, 47), k))
            cy += lh
        if s.get("caption"):
            self.block(d, t, .6 + s.get("type_time", 3.2) + .2, y0 + h + 50, s["caption"], "med", 46, th["muted"])

    def s_browser(self, d, t, s):
        """Browser walkthrough with callouts (concept illustration, not real client work)."""
        th = self.th
        y = self.headline(d, t, 0, 330, wrap(s["title"], font(th["head"], 76), W - 180), (), maxs=76)
        bx, by, bw, bh = 90, y + 40, W - 180, 620
        k = ease((t - .2) / .5)
        if k <= 0: return
        by += 40 * (1 - k)
        d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=24, fill=A(th["card"], k), outline=A(th["border"], k), width=3)
        for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
            d.ellipse([bx + 28 + i * 32, by + 26, bx + 48 + i * 32, by + 46], fill=A(c, k))
        d.rounded_rectangle([bx + 150, by + 18, bx + bw - 30, by + 54], radius=18, fill=A(th["border"], k))
        d.text((bx + 176, by + 23), s.get("url", "yourwebsite.com"), font=font("med", 24), fill=A(th["muted"], k))
        # loading bar
        lk = clamp((t - .5) / 1.2)
        d.rectangle([bx + 2, by + 70, bx + 2 + (bw - 4) * lk, by + 76], fill=A(th["accent"], k))
        cx0, cy0, cw = bx + 36, by + 110, bw - 72
        def bar(i, rect, col, rad=10):
            kk = ease((t - .7 - i * .08) / .4)
            if kk <= 0: return
            x1, y1, x2, y2 = rect
            d.rounded_rectangle([x1, y1, x1 + (x2 - x1) * kk, y2], radius=rad, fill=A(col, kk))
        bar(0, (cx0, cy0, cx0 + cw * .7, cy0 + 50), th["text"], 12)
        bar(1, (cx0, cy0 + 72, cx0 + cw * .5, cy0 + 100), th["muted"])
        bar(2, (cx0, cy0 + 130, cx0 + 220, cy0 + 186), th["accent"], 28)
        for j in range(3):
            bar(3 + j, (cx0 + j * (cw / 3), cy0 + 230, cx0 + j * (cw / 3) + cw / 3 - 20, cy0 + 440), th["border"], 16)
        if s.get("label"):
            self.pill(d, bx + bw - tw(s["label"], font("semi", 26)) - 100, by + bh - 40, s["label"], font("semi", 26),
                      th["muted"], th["bg_c"], k, h=50)
        # callouts
        cy = by + bh + 50
        for i, c in enumerate(s.get("callouts", [])[:4]):
            kk = ease((t - 1.6 - i * .45) / .45)
            if kk <= 0: continue
            yy = cy + i * 92
            self.check(d, 130, yy + 30, 28, kk, ease((t - 1.75 - i * .45) / .35), True)
            d.text((180 + 30 * (1 - kk), yy + 8), c, font=font("semi", 44), fill=A(th["text"], kk))


    def s_endscreen(self, d, t, s):
        """Branded end screen: logo mark, company name, tagline, WhatsApp contact."""
        th = self.th
        k = back(t / .6)
        r = 120 * k
        if r > 2:
            cx, cy = W / 2, 560
            d.rounded_rectangle([cx - r, cy - r, cx + r, cy + r], radius=r * .32, fill=A(th["accent"], 1))
            f = font("black", 120 * k); m = self.brand.get("mark", "SK")
            bb = d.textbbox((0, 0), m, font=f)
            fg = (255, 255, 255) if sum(th["accent"]) < 520 else (12, 12, 20)
            d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), m, font=f, fill=A(fg, 1))
        k1 = ease((t - .4) / .5)
        self.txt(d, None, 740 + 30 * (1 - k1), self.brand.get("name", "SK Developer"), font("black", 96), th["text"], k1)
        y = 870
        for i, l in enumerate(wrap(s.get("tagline", "Full-Stack Software & Digital Solutions"), font("med", 44), W - 200)):
            self.txt(d, None, y + i * 56, l, font("med", 44), th["muted"], ease((t - .6) / .5)); y2 = y + i * 56
        green = (37, 211, 102)
        kb = back((t - 1.0) / .6)
        if kb > .02:
            cy = 1150; bw, bh = 900 * kb, 150 * kb
            d.rounded_rectangle([W / 2 - bw / 2, cy - bh / 2, W / 2 + bw / 2, cy + bh / 2], radius=bh / 2, fill=A(green, 1))
            lab = s.get("button", "Discuss your project on WhatsApp").upper()
            ff = font("bold", 40 * kb)
            while tw(lab, ff) > bw - 80 and ff.size > 20: ff = font("bold", ff.size - 2)
            bb = d.textbbox((0, 0), lab, font=ff)
            d.text((W / 2 - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), lab, font=ff, fill=(255, 255, 255, 255))
        k3 = ease((t - 1.5) / .5)
        self.txt(d, None, 1265, self.brand.get("phone", "+92 325 2314412"), font("black", 72), th["text"], k3)
        self.txt(d, None, 1365, s.get("note", "wa.me/923252314412"), font("semi", 40), th["accent"] if sum(th["accent"]) > 150 else th["muted"], k3)

    def s_chat(self, d, t, s):
        """Chat conversation, e.g. an AI support chatbot (concept illustration)."""
        th = self.th
        y = self.headline(d, t, 0, 330, wrap(s["title"], font(th["head"], 76), W - 180), (), maxs=76)
        x0, y0, w = 90, y + 40, W - 90 - SAFE_R
        msgs = s["messages"]
        k = ease((t - .2) / .5)
        if k <= 0: return
        h = 120 + 150 * len(msgs)
        self.card(d, x0, y0, x0 + w, y0 + h, k)
        d.ellipse([x0 + 30, y0 + 28, x0 + 82, y0 + 80], fill=A(th["accent"], k))
        d.text((x0 + 100, y0 + 30), s.get("bot", "Support assistant"), font=font("bold", 36), fill=A(th["text"], k))
        if s.get("label"):
            lw = tw(s["label"], font("semi", 24)) + 68
            self.pill(d, x0 + w - lw - 24, y0 + 54, s["label"], font("semi", 24), th["muted"], th["bg_c"], k, h=44)
        cy = y0 + 120
        for i, m in enumerate(msgs):
            who, text = m[0], m[1]
            st = .7 + i * .9
            kk = ease((t - st) / .4)
            if kk <= 0: break
            # typing dots before bot replies
            lines = wrap(text, font("med", 38), w * .72)[:3]
            bh = 30 + 48 * len(lines)
            bw = max(tw(l, font("med", 38)) for l in lines) + 60
            user = who == "user"
            bx = x0 + w - 30 - bw if user else x0 + 30
            col = th["accent"] if user else th["border"]
            fg = (255, 255, 255) if user and sum(th["accent"]) < 520 else th["text"]
            d.rounded_rectangle([bx, cy + 20 * (1 - kk), bx + bw, cy + bh + 20 * (1 - kk)], radius=28, fill=A(col, kk))
            for j, l in enumerate(lines):
                d.text((bx + 30, cy + 16 + j * 48 + 20 * (1 - kk)), l, font=font("med", 38), fill=A(fg, kk))
            cy += bh + 22
        if s.get("caption"):
            self.block(d, t, .7 + len(msgs) * .9, y0 + h + 40, s["caption"], "med", 44, th["muted"])

    def s_dashboard(self, d, t, s):
        """Admin dashboard / CRM / booking / store mockup (concept illustration)."""
        th = self.th
        y = self.headline(d, t, 0, 330, wrap(s["title"], font(th["head"], 76), W - 180), (), maxs=76)
        x0, y0, w, h = 90, y + 40, W - 90 - SAFE_R, 700
        k = ease((t - .2) / .5)
        if k <= 0: return
        self.card(d, x0, y0, x0 + w, y0 + h, k)
        kind = s.get("kind", "admin")
        # sidebar
        d.rounded_rectangle([x0 + 20, y0 + 20, x0 + 200, y0 + h - 20], radius=18, fill=A(th["border"], k))
        for i, lab in enumerate(s.get("menu", ["Overview", "Orders", "Customers", "Reports"])[:6]):
            kk = ease((t - .5 - i * .1) / .4)
            col = th["accent"] if i == 0 else th["muted"]
            d.text((x0 + 40, y0 + 50 + i * 60), lab, font=font("semi", 26), fill=A(col, kk))
        mx, mw = x0 + 230, w - 250
        if kind == "booking":
            # calendar grid with booked slots
            days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
            cw = mw / 5
            for i, dd in enumerate(days):
                d.text((mx + i * cw + 10, y0 + 30), dd, font=font("semi", 26), fill=A(th["muted"], k))
            booked = [(0, 1), (1, 0), (1, 3), (2, 2), (3, 1), (3, 4), (4, 0), (4, 3), (2, 5), (0, 4)]
            for n, (c, r) in enumerate(booked):
                kk = ease((t - .7 - n * .12) / .35)
                if kk <= 0: continue
                bx, by = mx + c * cw + 6, y0 + 80 + r * 100
                d.rounded_rectangle([bx, by, bx + cw - 12, by + 84], radius=12, fill=A(th["accent"] if n % 3 else th["accent2"] if sum(th["accent2"]) < 700 else th["muted"], kk))
        elif kind == "store":
            for n in range(6):
                c, r = n % 3, n // 3
                kk = ease((t - .7 - n * .12) / .4)
                if kk <= 0: continue
                bx, by = mx + c * (mw / 3), y0 + 30 + r * 320
                d.rounded_rectangle([bx, by, bx + mw / 3 - 20, by + 200], radius=16, fill=A(th["border"], kk))
                d.rounded_rectangle([bx, by + 215, bx + 120, by + 235], radius=6, fill=A(th["muted"], kk))
                d.rounded_rectangle([bx + mw / 3 - 120, by + 250, bx + mw / 3 - 20, by + 290], radius=20, fill=A(th["accent"], kk))
        else:
            # KPI tiles (no numbers, to avoid fake figures) + bar chart
            for i in range(3):
                kk = ease((t - .6 - i * .12) / .4)
                if kk <= 0: continue
                bx = mx + i * (mw / 3)
                d.rounded_rectangle([bx, y0 + 30, bx + mw / 3 - 16, y0 + 150], radius=14, fill=A(th["border"], kk))
                d.rounded_rectangle([bx + 20, y0 + 60, bx + 120, y0 + 76], radius=6, fill=A(th["muted"], kk))
                d.rounded_rectangle([bx + 20, y0 + 96, bx + 80 + 40 * i, y0 + 126], radius=8, fill=A(th["accent"], kk))
            vals = [.45, .7, .55, .9, .65, .8, .6]
            bw = mw / len(vals)
            for j, v in enumerate(vals):
                kk = ease((t - .9 - j * .07) / .5)
                hh = 380 * v * kk
                if hh > 1:
                    bx = mx + j * bw
                    d.rounded_rectangle([bx + 6, y0 + h - 40 - hh, bx + bw - 10, y0 + h - 40], radius=8,
                                        fill=A(th["accent"] if j % 2 else th["muted"], 1))
        if s.get("label"):
            lw = tw(s["label"], font("semi", 24)) + 68
            self.pill(d, x0 + w - lw - 24, y0 + h - 46, s["label"], font("semi", 24), th["muted"], th["bg_c"], k, h=44)
        cy = y0 + h + 50
        for i, c in enumerate(s.get("callouts", [])[:3]):
            kk = ease((t - 1.6 - i * .45) / .45)
            if kk <= 0: continue
            yy = cy + i * 90
            self.check(d, 130, yy + 30, 28, kk, ease((t - 1.75 - i * .45) / .35), True)
            d.text((180 + 30 * (1 - kk), yy + 8), c, font=font("semi", 44), fill=A(th["text"], kk))

    # ---- captions (burned-in subtitles of the voiceover)
    def captions(self, d, i, t):
        sc = self.scenes[i]
        if not self.caps[i] or sc.get("captions") is False or (sc["type"] in ("cta", "endscreen") and not sc.get("captions")):
            return
        th = self.th; style = self.lay.get("captions", "box")
        for (a, b, txt) in self.caps[i]:
            if a <= t < b + .05:
                k = ease((t - a) / .12)
                f = font("xb", 54)
                lines = wrap(txt, f, W - 300)[:2]
                y = 1440 - (len(lines) - 1) * 42
                for j, l in enumerate(lines):
                    w = tw(l, f); x = (W - SAFE_R + 40 - w) / 2; yy = y + j * 84
                    if style == "box":
                        d.rounded_rectangle([x - 26, yy - 10, x + w + 26, yy + 66], radius=18, fill=A((10, 10, 12), .82 * k))
                        d.text((x, yy), l, font=f, fill=A((255, 255, 255), k))
                    elif style == "bar":
                        d.rounded_rectangle([x - 26, yy - 10, x + w + 26, yy + 66], radius=8, fill=A(th["accent"], .95 * k))
                        fg = (255, 255, 255) if sum(th["accent"]) < 520 else (12, 12, 20)
                        d.text((x, yy), l, font=f, fill=A(fg, k))
                    else:
                        for ox, oy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2), (2, -2), (-2, 2)):
                            d.text((x + ox, yy + oy), l, font=f, fill=A((0, 0, 0), k))
                        d.text((x, yy), l, font=f, fill=A((255, 214, 0) if j == 0 else (255, 255, 255), k))
                return

    # ---- new visual scenes: illustrated character, search typing, icon grid
    def s_character(self, d, t, s):
        th = self.th
        y = self.headline(d, t, 0, 300, wrap(s.get("title", ""), font(th["head"], 76), W - 220), tuple(s.get("accent", [])), maxs=76) if s.get("title") else 300
        # typed bubble / editor card
        lines = s.get("typed", [])
        if lines:
            k = ease((t - .3) / .5)
            x0, y0, x1 = 110, y + 40, W - SAFE_R - 20
            h = 70 + 62 * len(lines)
            self.card(d, x0, y0 + 30 * (1 - k), x1, y0 + h + 30 * (1 - k), k, active=True)
            total = sum(len(l) for l in lines)
            n = int(total * clamp((t - .7) / max(1.0, s.get("type_time", 2.2))))
            yy = y0 + 36; fT = font("semi", 46); cur = None
            for l in lines:
                show = l[:max(0, n)]
                if cur is None and len(show) < len(l): cur = (x0 + 44 + tw(show, fT), yy)
                n -= len(l)
                d.text((x0 + 40, yy), show, font=fT, fill=A(th["text"], k))
                yy += 62
            if cur is None: cur = (x0 + 44 + tw(lines[-1], fT), yy - 62)
            if int(t * 2.5) % 2 == 0: d.rectangle([cur[0], cur[1] + 4, cur[0] + 6, cur[1] + 52], fill=A(th["accent"], k))
            y = y0 + h + 30
        kc = back((t - .1) / .7)
        sc = s.get("scale", 1.2) * max(.01, kc)
        base_y = min(1330, y + 470 * s.get("scale", 1.2))
        if kc > .02:
            art.character(d, W / 2 - 40, base_y, sc, t, th, skin=s.get("skin", 1), typing=s.get("pose", "typing") == "typing",
                          shirt=hexc(s["shirt"]) if s.get("shirt") else None, wave=s.get("pose") == "wave")
        for j, (ic, ang) in enumerate(zip(s.get("icons", []), (-165, -15, 15, 165))):
            kk = back((t - .8 - j * .25) / .5)
            if kk <= .02: continue
            r = 420 * s.get("scale", 1.2) * .75
            cx = W / 2 - 40 + math.cos(math.radians(ang)) * r * 1.15
            cy = base_y - 330 * s.get("scale", 1.2) + math.sin(math.radians(ang)) * r * .55 + math.sin(t * 2 + j) * 10
            cx = min(cx, W - SAFE_R - 70)
            rr = 62 * kk
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=A(th["card"], 1), outline=A(th["accent"], 1), width=4)
            art.icon(d, ic, cx, cy, 64 * kk, th["accent"], 1)

    def s_search(self, d, t, s):
        th = self.th
        y = self.headline(d, t, 0, 320, wrap(s.get("title", ""), font(th["head"], 76), W - 220), tuple(s.get("accent", [])), maxs=76)
        k = ease((t - .2) / .5)
        x0, x1, y0 = 100, W - SAFE_R, y + 60
        d.rounded_rectangle([x0, y0, x1, y0 + 130], radius=65, fill=A(th["card"], k), outline=A(th["accent"], k), width=4)
        art.icon(d, "search", x0 + 75, y0 + 65, 54, th["accent"], k)
        q = s.get("query", "")
        n = int(len(q) * clamp((t - .6) / max(.8, .06 * len(q))))
        f = font("semi", 48); shown = q[:n]
        while tw(shown, f) > x1 - x0 - 200 and len(shown) > 3: shown = shown[1:]
        d.text((x0 + 140, y0 + 36), shown, font=f, fill=A(th["text"], k))
        if int(t * 2.5) % 2 == 0 and k > .5:
            cx = x0 + 146 + tw(shown, f); d.rectangle([cx, y0 + 38, cx + 6, y0 + 94], fill=A(th["accent"], 1))
        if s.get("label"): self.pill(d, x1 - tw(s["label"], font("semi", 24)) - 68, y0 + 170, s["label"], font("semi", 24), th["muted"], th["bg_c"], k, h=44)
        t0 = .6 + .06 * len(q) + .3
        yy = y0 + 230
        for i, it in enumerate(s.get("results", [])[:4]):
            title, sub, ic = (it + ["", "globe"])[:3]
            kk = ease((t - t0 - i * .4) / .45)
            if kk <= 0: continue
            hh = 170
            self.card(d, x0, yy + 30 * (1 - kk), x1, yy + hh + 30 * (1 - kk), kk, active=i == s.get("highlight", -1))
            cy = yy + hh / 2 + 30 * (1 - kk)
            d.rounded_rectangle([x0 + 30, cy - 50, x0 + 130, cy + 50], radius=24, fill=A(th["accent"], kk))
            art.icon(d, ic, x0 + 80, cy, 54, (255, 255, 255) if sum(th["accent"]) < 520 else (12, 12, 20), kk)
            d.text((x0 + 160, cy - 52), wrap(title, font("bold", 44), x1 - x0 - 200)[0], font=font("bold", 44), fill=A(th["text"], kk))
            d.text((x0 + 160, cy + 6), wrap(sub, font("reg", 34), x1 - x0 - 200)[0], font=font("reg", 34), fill=A(th["muted"], kk))
            yy += hh + 26

    def s_icons(self, d, t, s):
        th = self.th
        y = self.headline(d, t, 0, 360, wrap(s.get("title", ""), font(th["head"], 80), W - 220), tuple(s.get("accent", [])), maxs=80)
        if s.get("sub"): y = self.block(d, t, .2, y + 10, s["sub"], "med", 42, th["muted"])
        items = s.get("items", [])[:6]; cols = 2 if len(items) <= 4 else 3
        gw = (W - 90 - SAFE_R - 30 * (cols - 1)) / cols; gh = 250
        for i, (ic, lab) in enumerate(items):
            r_, c_ = divmod(i, cols)
            kk = back((t - .4 - i * .22) / .45)
            if kk <= .02: continue
            x0 = 90 + c_ * (gw + 30); y0 = y + 60 + r_ * (gh + 30)
            cx, cy = x0 + gw / 2, y0 + gh / 2
            ww, hh = gw * kk, gh * kk
            self.card(d, cx - ww / 2, cy - hh / 2, cx + ww / 2, cy + hh / 2, 1, active=i == 0)
            art.icon(d, ic, cx, cy - 40 * kk, 80 * kk, th["accent"], 1)
            ff = font("semi", (40 if cols == 2 else 34) * kk)
            for j, l in enumerate(wrap(lab, ff, gw - 30)[:2]):
                self.txt(d, cx - tw(l, ff) / 2, cy + 30 * kk + j * 44 * kk, l, ff, th["text"], 1)

    # ---- frame
    def frame(self, i, t):
        s = self.scenes[i]; dur = self.durs[i]
        gt = self.starts[i] + t
        img = self.background(gt)
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
        getattr(self, "s_" + s["type"])(d, t, s)
        if i < len(self.scenes) - 1:
            m = clamp((dur - t) / .35)
            if m < 1:
                if self.th["exit"] == "slide":
                    L = L.transform((W, H), Image.AFFINE, (1, 0, 160 * (1 - m), 0, 1, 0))
                L.putalpha(L.getchannel("A").point(lambda v: int(v * m)))
        img.alpha_composite(L)
        H2 = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d2 = ImageDraw.Draw(H2)
        self.header(d2, gt); self.progress(d2, gt)
        self.captions(d2, i, t)
        img.alpha_composite(H2)
        rgb = img.convert("RGB")
        blk = (255, 255, 255) if self.light else (0, 0, 0)
        if gt < .4: rgb = Image.blend(Image.new("RGB", (W, H), blk), rgb, gt / .4)
        if gt > self.total - .6: rgb = Image.blend(Image.new("RGB", (W, H), blk), rgb, clamp((self.total - gt) / .6))
        return rgb

# ------------------------------------------------------------------ music
SR = 44100
def music(path, dur, mood="corporate", seed=1):
    from scipy.io import wavfile
    from scipy.signal import fftconvolve, butter, lfilter
    rng = np.random.default_rng(seed)
    def hz(m): return 440 * 2 ** ((m - 69) / 12)
    def lp(x, fc):
        b, a = butter(2, fc / (SR / 2)); return lfilter(b, a, x)
    def hp(x, fc):
        b, a = butter(2, fc / (SR / 2), btype="high"); return lfilter(b, a, x)
    def add(buf, st, sig):
        i = int(st * SR)
        if i >= len(buf) or i < 0: return
        j = min(len(buf), i + len(sig)); buf[i:j] += sig[:j - i]
    def envl(n, a, r):
        e = np.ones(n); na, nr = max(1, int(a * SR)), max(1, int(r * SR))
        e[:na] = np.linspace(0, 1, na)
        if nr < n: e[-nr:] *= np.linspace(1, 0, nr)
        return e

    P = {
        "corporate": dict(bpm=(98, 108), prog=[[0, 4, 7, 12], [-1, 2, 7, 11], [-3, 0, 4, 9], [-7, -3, 0, 5]], roots=[0, -1, -3, -7],
                          lead="pluck", drums="four", swing=0, crackle=0, pad=.035),
        "lofi": dict(bpm=(78, 88), prog=[[2, 5, 9, 12], [-5, -1, 2, 5], [0, 4, 7, 11], [-3, 0, 4, 7]], roots=[2, -5, 0, -3],
                     lead="keys", drums="hiphop", swing=.12, crackle=1, pad=.03),
        "house": dict(bpm=(118, 124), prog=[[0, 3, 7, 12], [-4, 0, 3, 8], [-9, -5, 0, 3], [-2, 2, 5, 10]], roots=[0, -4, -9, -2],
                      lead="stab", drums="house", swing=0, crackle=0, pad=.025),
        "chill": dict(bpm=(88, 96), prog=[[0, 4, 7, 11], [-3, 0, 4, 7], [5, 9, 12, 16], [-5, -1, 2, 7]], roots=[0, -3, 5, -5],
                      lead="bell", drums="light", swing=.06, crackle=0, pad=.04),
        "upbeat": dict(bpm=(112, 120), prog=[[0, 4, 7, 12], [-3, 0, 4, 9], [-7, -3, 0, 5], [-5, -1, 2, 7]], roots=[0, -3, -7, -5],
                       lead="pluck", drums="pop", swing=0, crackle=0, pad=.03),
    }[mood]
    bpm = rng.uniform(*P["bpm"]); beat = 60 / bpm; bar = beat * 4
    key = 60 + int(rng.integers(-5, 6))
    N = int(SR * dur)
    pad = np.zeros(N); bass = np.zeros(N); lead = np.zeros(N); dr = np.zeros(N)
    order = list(range(4))
    if rng.random() < .4: order = [0, 2, 3, 1] if mood != "lofi" else order
    nbars = int(np.ceil(dur / bar))
    motif = [int(x) for x in rng.integers(0, 4, 8)]
    for b in range(nbars):
        t0 = b * bar; ci = order[b % 4]
        ch = [key + x for x in P["prog"][ci]]; root = key - 24 + P["roots"][ci]
        n = int(bar * SR); tt = np.arange(n) / SR
        s = np.zeros(n)
        for m in ch:
            for det in (-.08, .08):
                f = hz(m + det)
                for h, amp in ((1, 1), (2, .3), (3, .12)):
                    s += amp * np.sin(2 * np.pi * f * h * tt + rng.random() * 6)
        add(pad, t0, s * envl(n, .35, .35) * P["pad"])
        # bass
        bpat = {"four": range(8), "house": [1, 3, 5, 7], "hiphop": [0, 3, 5], "light": [0, 4], "pop": range(8)}[P["drums"]]
        for k in bpat:
            nn = int(beat / 2 * SR) if P["drums"] != "light" else int(beat * 2 * SR); t2 = np.arange(nn) / SR
            f = hz(root + (12 if (k % 4 == 3 and P["drums"] in ("four", "pop")) else 0))
            sb = (np.sin(2 * np.pi * f * t2) + .3 * np.sin(4 * np.pi * f * t2)) * np.exp(-t2 * (3 if P["drums"] == "light" else 5)) * envl(nn, .005, .03)
            add(bass, t0 + k * beat / 2, sb * .22)
        # lead
        if b >= 1:
            for k in range(8):
                if P["lead"] == "stab" and k % 2 == 0: continue
                if P["lead"] in ("keys", "bell") and k % 2 == 1 and rng.random() < .5: continue
                sw = P["swing"] * beat if k % 2 else 0
                m = ch[motif[k] % 4] + (12 if P["lead"] != "keys" else 0)
                f = hz(m)
                if P["lead"] == "stab":
                    nn = int(.22 * SR); t3 = np.arange(nn) / SR
                    sp = sum(np.sin(2 * np.pi * hz(x + 12) * t3) for x in ch[1:]) * np.exp(-t3 * 12) * .02
                elif P["lead"] == "keys":
                    nn = int(.9 * SR); t3 = np.arange(nn) / SR
                    sp = (np.sin(2 * np.pi * f * t3 + .6 * np.sin(2 * np.pi * f * 2 * t3) * np.exp(-t3 * 4))) * np.exp(-t3 * 3.5) * .05
                elif P["lead"] == "bell":
                    nn = int(1.2 * SR); t3 = np.arange(nn) / SR
                    sp = (np.sin(2 * np.pi * f * t3) + .4 * np.sin(2 * np.pi * f * 2.76 * t3) * np.exp(-t3 * 6)) * np.exp(-t3 * 2.5) * .04
                else:
                    nn = int(.6 * SR); t3 = np.arange(nn) / SR
                    sp = (np.sin(2 * np.pi * f * t3) + .25 * np.sin(4 * np.pi * f * t3)) * np.exp(-t3 * 7) * .06
                add(lead, t0 + k * beat / 2 + sw, sp * envl(len(sp), .003, .05))
        # drums
        if b >= 2 or (P["drums"] == "light" and b >= 1):
            def kick(at, g=.5):
                nn = int(.35 * SR); tk = np.arange(nn) / SR
                fk = 50 + 90 * np.exp(-tk * 30)
                add(dr, at, np.sin(2 * np.pi * np.cumsum(fk) / SR) * np.exp(-tk * 9) * g)
            def snare(at, g=.12):
                nn = int(.25 * SR); tc = np.arange(nn) / SR
                add(dr, at, hp(rng.standard_normal(nn), 1200) * np.exp(-tc * 18) * g)
            def hat(at, g=.06, dec=60):
                nn = int(.1 * SR); th = np.arange(nn) / SR
                add(dr, at, hp(rng.standard_normal(nn), 7000) * np.exp(-th * dec) * g)
            for k in range(4):
                bt = t0 + k * beat
                kind = P["drums"]
                if kind in ("four", "house", "pop"):
                    kick(bt)
                    if k in (1, 3): snare(bt)
                    hat(bt + beat / 2, .07 if kind != "house" else .09, 60 if kind != "house" else 25)
                    if kind == "pop": hat(bt, .03)
                elif kind == "hiphop":
                    if k in (0, 2): kick(bt, .55)
                    if k == 2: kick(bt + beat * .75, .35)
                    if k in (1, 3): snare(bt, .15)
                    hat(bt, .05); hat(bt + beat / 2 + P["swing"] * beat, .035)
                elif kind == "light":
                    if k == 0: kick(bt, .35)
                    if k == 2: snare(bt, .06)
                    hat(bt + beat / 2, .03)
    tt = np.arange(N) / SR
    pump = np.ones(N)
    if P["drums"] in ("four", "house", "pop"):
        st = 2 * bar; ph = ((tt - st) % beat) / beat; m = tt >= st
        pump[m] = .55 + .45 * np.clip(ph[m] / .45, 0, 1)
    pad = lp(pad, 2400 if mood != "lofi" else 1400) * pump
    lead = lead * (.7 + .3 * pump)
    if mood == "lofi": lead = lp(lead, 2500)
    bass = lp(bass, 400)
    irn = int(1.6 * SR)
    ir = lp(rng.standard_normal(irn) * np.exp(-np.arange(irn) / SR * 3.5), 5000)
    ir /= np.abs(ir).sum() / 8
    wet = fftconvolve(pad + lead, ir)[:N] * .25
    extra = np.zeros(N)
    if P["crackle"]:
        idx = rng.integers(0, N, int(dur * 25))
        extra[idx] = rng.uniform(-.25, .25, len(idx))
        extra = lp(extra, 4000) + lp(rng.standard_normal(N), 800) * .004
    Lc = pad + lead + bass + dr + wet + extra
    Rc = pad * .95 + np.roll(lead, int(.012 * SR)) + bass + dr + np.roll(wet, int(.017 * SR)) + extra
    mix = np.stack([Lc, Rc], 1)
    fi, fo = int(1.0 * SR), int(2.5 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    mix = np.tanh(mix * 1.2); mix /= np.abs(mix).max(); mix *= .7
    wavfile.write(path, SR, (mix * 32767).astype(np.int16))

def mix_voice(r, path):
    """Lay the per-scene voiceover over the music and duck the music under the voice."""
    from scipy.io import wavfile
    from scipy.signal import resample_poly
    sr, mus = wavfile.read(path); mus = mus.astype(np.float32) / 32767
    if mus.ndim == 1: mus = mus[:, None]
    vo = np.zeros(len(mus), np.float32)
    for i, a in enumerate(r.vo):
        if a is None: continue
        a = resample_poly(a, sr, r.vsr).astype(np.float32)
        st = int((r.starts[i] + (VO_LEAD if i else 0.15)) * sr)
        e = min(len(vo), st + len(a)); vo[st:e] += a[:e - st]
    env = (np.abs(vo) > .02).astype(np.float32)
    k = int(sr * .25); env = np.convolve(env, np.ones(k) / k, mode="same").clip(0, 1)
    duck = 1 - .72 * env
    out = mus * duck[:, None] * .55 + vo[:, None] * .95
    out /= max(1e-6, np.abs(out).max()); out *= .92
    wavfile.write(path, sr, (out * 32767).astype(np.int16))

# ------------------------------------------------------------------ main
def render(spec, out):
    r = R(spec)
    r.frame(0, max(.5, r.durs[0] - .5)).save(os.path.join(os.path.dirname(out) or ".", "thumbnail.jpg"), quality=90)
    work = tempfile.mkdtemp(prefix="gen_")
    parts = []
    for i in range(len(r.scenes)):
        tmp, fin = f"{work}/s{i}.tmp.mp4", f"{work}/s{i}.mp4"
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                              "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                              "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        for n in range(int(round(r.durs[i] * FPS))):
            p.stdin.write(r.frame(i, n / FPS).tobytes())
        p.stdin.close()
        if p.wait() != 0: raise SystemExit("ffmpeg failed on scene %d" % i)
        os.rename(tmp, fin); parts.append(fin)
    with open(f"{work}/list.txt", "w") as fh:
        for pth in parts: fh.write(f"file '{pth}'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{work}/list.txt", "-c", "copy",
                    f"{work}/v.mp4"], check=True)
    m = spec.get("music", {})
    music(f"{work}/m.wav", r.total, m.get("mood", "corporate"), int(m.get("seed", 1)))
    if any(a is not None for a in r.vo): mix_voice(r, f"{work}/m.wav")
    tmp_out = out[:-4] + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{work}/v.mp4", "-i", f"{work}/m.wav", "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-af", "loudnorm=I=-16:TP=-1.5", "-shortest",
                    "-movflags", "+faststart", tmp_out], check=True)
    os.rename(tmp_out, out)
    shutil.rmtree(work, ignore_errors=True)
    print(f"OK {out} {r.total:.1f}s")

def preview(spec, out):
    r = R(spec)
    ims = []
    for i in range(len(r.scenes)):
        ims.append(r.frame(i, r.durs[i] - .45).resize((360, 640)))
    cols = 4; rows = (len(ims) + cols - 1) // cols
    c = Image.new("RGB", (360 * cols, 640 * rows), (40, 40, 40))
    for n, im in enumerate(ims): c.paste(im, ((n % cols) * 360, (n // cols) * 640))
    p = out[:-4] + "_preview.jpg"; c.save(p, quality=85)
    print(f"PREVIEW {p} total {r.total:.1f}s")

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    if "--preview" in sys.argv: preview(spec, out)
    else: render(spec, out)
