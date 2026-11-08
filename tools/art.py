"""Vector icons and a flat illustrated character for gen.py (drawn with PIL, no external assets).

The character is a generic cartoon developer, not a real person.
"""
import math
from PIL import ImageDraw

def _A(c, a): return tuple(c[:3]) + (int(255 * max(0, min(1, a))),)

ICONS = ["cart", "chat", "calendar", "chart", "code", "lock", "rocket", "phone", "globe", "gear", "bolt", "search",
         "user", "card", "mail", "star", "clock", "layout", "server", "wordpress", "bag", "speed", "shield", "link", "bot"]

def icon(d, name, cx, cy, s, col, a=1.0, w=None):
    """Line icon centred at (cx, cy), box size s."""
    if s <= 2: return  # nothing visible yet (scale-in can dip to or below 0)
    c = _A(col, a); w = w or max(3, int(s * .085)); r = s / 2
    def L(*pts): d.line([(cx + x * r, cy + y * r) for x, y in pts], fill=c, width=w, joint="curve")
    def RR(x0, y0, x1, y1, rad=.15, fill=None):
        try:
            d.rounded_rectangle([cx + x0 * r, cy + y0 * r, cx + x1 * r, cy + y1 * r], radius=rad * r, outline=c, width=w,
                                fill=_A(fill, a) if fill else None)
        except ValueError:  # tiny icon mid scale-in: stroke wider than the shape (e.g. "link" pill)
            pass
    def E(x0, y0, x1, y1, fill=False): d.ellipse([cx + x0 * r, cy + y0 * r, cx + x1 * r, cy + y1 * r], outline=c, width=w, fill=c if fill else None)
    def ARC(x0, y0, x1, y1, a0, a1): d.arc([cx + x0 * r, cy + y0 * r, cx + x1 * r, cy + y1 * r], a0, a1, fill=c, width=w)
    if name == "cart":
        L((-.95, -.7), (-.65, -.7), (-.4, .35), (.65, .35), (.85, -.4), (-.5, -.4)); E(-.4, .55, -.15, .8, True); E(.35, .55, .6, .8, True)
    elif name == "bag":
        RR(-.7, -.35, .7, .85, .12); ARC(-.35, -.85, .35, -.1, 180, 360)
    elif name == "chat":
        RR(-.85, -.7, .85, .45, .3); L((-.35, .45), (-.55, .85), (.05, .45)); [E(x - .09, -.21, x + .09, -.03, True) for x in (-.4, 0, .4)]
    elif name == "bot":
        RR(-.7, -.4, .7, .7, .25); L((0, -.4), (0, -.75)); E(-.1, -.95, .1, -.75, True); E(-.4, -.05, -.15, .2, True); E(.15, -.05, .4, .2, True); L((-.25, .45), (.25, .45))
    elif name == "calendar":
        RR(-.8, -.65, .8, .85, .12); L((-.8, -.25), (.8, -.25)); L((-.4, -.9), (-.4, -.5)); L((.4, -.9), (.4, -.5))
        for i in range(3):
            for j in range(2): E(-.55 + i * .45, .05 + j * .38, -.4 + i * .45, .2 + j * .38, True)
    elif name == "chart":
        L((-.85, -.85), (-.85, .85), (.85, .85)); L((-.55, .4), (-.15, -.05), (.15, .2), (.7, -.55)); L((.4, -.55), (.7, -.55), (.7, -.25))
    elif name == "code":
        L((-.35, -.55), (-.85, 0), (-.35, .55)); L((.35, -.55), (.85, 0), (.35, .55)); L((.12, -.7), (-.12, .7))
    elif name == "lock":
        RR(-.65, -.1, .65, .85, .15); ARC(-.42, -.8, .42, .2, 180, 360); L((-.42, -.3), (-.42, -.1)); L((.42, -.3), (.42, -.1)); L((0, .25), (0, .5))
    elif name == "shield":
        L((0, -.9), (.75, -.6), (.65, .2), (0, .9), (-.65, .2), (-.75, -.6), (0, -.9)); L((-.3, 0), (-.05, .28), (.38, -.25))
    elif name == "rocket":
        L((0, -.95), (.35, -.45), (.35, .35), (-.35, .35), (-.35, -.45), (0, -.95)); E(-.13, -.35, .13, -.09)
        L((-.35, .05), (-.7, .45), (-.35, .35)); L((.35, .05), (.7, .45), (.35, .35)); L((-.15, .55), (0, .9), (.15, .55))
    elif name == "phone":
        RR(-.5, -.92, .5, .92, .22); L((-.15, .68), (.15, .68))
    elif name == "globe":
        E(-.85, -.85, .85, .85); L((-.85, 0), (.85, 0)); ARC(-.4, -.85, .4, .85, 0, 360); L((-.72, -.45), (.72, -.45)); L((-.72, .45), (.72, .45))
    elif name == "gear":
        for k in range(8):
            ang = k * math.pi / 4; L((math.cos(ang) * .55, math.sin(ang) * .55), (math.cos(ang) * .9, math.sin(ang) * .9))
        E(-.62, -.62, .62, .62); E(-.25, -.25, .25, .25)
    elif name == "bolt":
        L((.15, -.95), (-.55, .1), (0, .1), (-.15, .95), (.55, -.1), (0, -.1), (.15, -.95))
    elif name == "speed":
        ARC(-.9, -.75, .9, 1.05, 180, 360); L((0, .15), (.5, -.4)); E(-.12, .03, .12, .27, True)
    elif name == "search":
        E(-.8, -.8, .35, .35); L((.25, .25), (.85, .85))
    elif name == "user":
        E(-.38, -.9, .38, -.14); ARC(-.8, .05, .8, 1.6, 180, 360)
    elif name == "card":
        RR(-.9, -.6, .9, .6, .12); L((-.9, -.22), (.9, -.22)); L((-.6, .3), (-.15, .3))
    elif name == "mail":
        RR(-.9, -.6, .9, .6, .1); L((-.85, -.5), (0, .1), (.85, -.5))
    elif name == "star":
        pts = []
        for k in range(10):
            rr = .9 if k % 2 == 0 else .38; ang = -math.pi / 2 + k * math.pi / 5
            pts.append((math.cos(ang) * rr, math.sin(ang) * rr))
        L(*(pts + [pts[0]]))
    elif name == "clock":
        E(-.85, -.85, .85, .85); L((0, -.5), (0, 0), (.4, .25))
    elif name == "layout":
        RR(-.85, -.75, .85, .75, .1); L((-.85, -.35), (.85, -.35)); L((-.25, -.35), (-.25, .75))
    elif name == "server":
        RR(-.8, -.85, .8, -.1, .12); RR(-.8, .1, .8, .85, .12); E(-.55, -.55, -.35, -.35, True); E(-.55, .4, -.35, .6, True)
    elif name == "link":
        RR(-.95, -.3, .15, .3, .5); RR(-.15, -.3, .95, .3, .5)
    elif name == "wordpress":
        E(-.88, -.88, .88, .88); L((-.55, -.35), (-.25, .55), (0, -.1), (.25, .55), (.55, -.35))
    else:
        E(-.6, -.6, .6, .6)

SKIN = [(241, 194, 158), (198, 140, 101), (141, 94, 62), (224, 172, 128)]

def character(d, cx, base_y, sc, t, th, skin=1, typing=True, shirt=None, hair=(34, 30, 30), wave=False):
    """Flat cartoon developer sitting at a laptop. base_y = desk top. sc = scale (1 ~ 520 px wide)."""
    sk = SKIN[skin % len(SKIN)]
    shirt = shirt or th["accent"]
    S = lambda v: v * sc
    # chair back
    d.rounded_rectangle([cx - S(150), base_y - S(330), cx + S(150), base_y + S(40)], radius=S(40), fill=_A(th["border"], 1))
    # body
    d.rounded_rectangle([cx - S(120), base_y - S(240), cx + S(120), base_y + S(20)], radius=S(70), fill=_A(shirt, 1))
    # neck + head
    d.rectangle([cx - S(22), base_y - S(275), cx + S(22), base_y - S(230)], fill=_A(sk, 1))
    bob = math.sin(t * 2.2) * S(4)
    hx, hy, hr = cx, base_y - S(345) + bob, S(78)
    d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=_A(sk, 1))
    d.chord([hx - hr - S(4), hy - hr - S(10), hx + hr + S(4), hy + hr * .55], 180, 360, fill=_A(hair, 1))
    d.ellipse([hx - hr - S(8), hy - S(10), hx - hr + S(14), hy + S(26)], fill=_A(sk, 1))  # ear
    d.ellipse([hx + hr - S(14), hy - S(10), hx + hr + S(8), hy + S(26)], fill=_A(sk, 1))
    blink = (t % 3.2) > 3.05
    for ex in (-S(28), S(28)):
        if blink: d.line([hx + ex - S(9), hy + S(10), hx + ex + S(9), hy + S(10)], fill=_A((25, 25, 30), 1), width=max(2, int(S(5))))
        else: d.ellipse([hx + ex - S(8), hy + S(2), hx + ex + S(8), hy + S(18)], fill=_A((25, 25, 30), 1))
    d.arc([hx - S(26), hy + S(14), hx + S(26), hy + S(50)], 20, 160, fill=_A((120, 60, 50), 1), width=max(2, int(S(5))))
    # laptop (back of screen faces viewer)
    lw, lh = S(300), S(190)
    d.rounded_rectangle([cx - lw / 2, base_y - lh, cx + lw / 2, base_y], radius=S(16), fill=_A((40, 42, 48), 1))
    d.ellipse([cx - S(16), base_y - lh / 2 - S(16), cx + S(16), base_y - lh / 2 + S(16)], fill=_A(th["accent"], 1))
    # desk
    d.rounded_rectangle([cx - S(330), base_y, cx + S(330), base_y + S(26)], radius=S(10), fill=_A(th["muted"], 1))
    # arms + typing hands
    for side in (-1, 1):
        ph = t * 14 + (0 if side < 0 else math.pi)
        lift = (abs(math.sin(ph)) * S(12)) if typing else 0
        if wave and side > 0:
            ang = math.sin(t * 6) * .5
            ex, ey = cx + S(150), base_y - S(260)
            hxp, hyp = ex + math.sin(ang) * S(40), ey - S(120)
            d.line([cx + S(95), base_y - S(170), ex, ey, hxp, hyp], fill=_A(shirt, 1), width=int(S(44)), joint="curve")
            d.ellipse([hxp - S(30), hyp - S(30), hxp + S(30), hyp + S(30)], fill=_A(sk, 1))
            continue
        sx, sy = cx + side * S(95), base_y - S(170)
        hx2, hy2 = cx + side * S(70), base_y - S(16) - lift
        d.line([sx, sy, cx + side * S(150), base_y - S(60), hx2, hy2], fill=_A(shirt, 1), width=int(S(44)), joint="curve")
        d.ellipse([hx2 - S(28), hy2 - S(22), hx2 + S(28), hy2 + S(22)], fill=_A(sk, 1))
    # coffee mug
    mx = cx + S(255)
    d.rounded_rectangle([mx - S(30), base_y - S(70), mx + S(30), base_y], radius=S(8), fill=_A(th["accent2"], 1))
    d.arc([mx + S(18), base_y - S(55), mx + S(50), base_y - S(20)], 270, 90, fill=_A(th["accent2"], 1), width=max(2, int(S(8))))
    for k in range(2):
        yy = base_y - S(90) - ((t * 40 + k * 30) % S(60))
        d.arc([mx - S(14) + k * S(14), yy - S(20), mx + S(6) + k * S(14), yy + S(20)], 90, 270, fill=_A(th["muted"], .6), width=max(2, int(S(4))))
