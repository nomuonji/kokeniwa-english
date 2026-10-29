# -*- coding: utf-8 -*-
"""OGP画像(1200x630)とブログのカードサムネを、サイト・Instagram と同じポップなテイストで描く。

build_og_images.py から呼ばれる。描画の部品(丸ゴシック・こけまる・マスキングテープ・
キラキラ)は ig_cards.py と共通。
  - パステルの地に水玉、白いステッカー風カード(縁取り＋ずらした影)
  - タイトルは丸ゴシックで、行ごとに蛍光ペン
  - 右下からこけまるがのぞく(SNSのタイムラインで縮んでも目印になる)
"""
from PIL import Image, ImageDraw

import ig_cards as ic

W, H = 1200, 630
SS = ic.SS

# サイトの pop.css / Instagram カードと同じ配色
PALETTES = {
    "moss":   {"bg": (232, 243, 220), "dot": (216, 234, 200), "accent": (95, 154, 67),
               "deep": (63, 109, 44), "mark": (212, 236, 190), "tape": (255, 214, 120)},
    "lav":    {"bg": (236, 232, 252), "dot": (222, 215, 248), "accent": (132, 110, 214),
               "deep": (86, 66, 160), "mark": (218, 208, 252), "tape": (255, 200, 140)},
    "mint":   {"bg": (220, 243, 236), "dot": (200, 233, 223), "accent": (52, 168, 146),
               "deep": (36, 112, 99), "mark": (176, 236, 218), "tape": (255, 214, 120)},
    "peach":  {"bg": (254, 236, 224), "dot": (250, 220, 203), "accent": (232, 128, 88),
               "deep": (166, 82, 52), "mark": (255, 208, 182), "tape": (150, 210, 200)},
    "lemon":  {"bg": (255, 245, 206), "dot": (252, 234, 178), "accent": (232, 160, 30),
               "deep": (160, 104, 18), "mark": (255, 226, 130), "tape": (246, 170, 190)},
    "sakura": {"bg": (255, 236, 241), "dot": (252, 218, 228), "accent": (236, 112, 146),
               "deep": (168, 62, 98), "mark": (255, 204, 218), "tape": (150, 214, 196)},
}

CARD = [44, 46, W - 60, H - 58]


class OgCanvas(ic.Canvas):
    def __init__(self, bg):
        self.img = Image.new("RGB", (W * SS, H * SS), bg)
        self.d = ImageDraw.Draw(self.img, "RGBA")

    def done(self):
        return self.img.resize((W, H), Image.LANCZOS)


def _dots(cv, pal):
    step = 64
    for row, y in enumerate(range(-10, H + 40, step)):
        off = step / 2 if row % 2 else 0
        for x in range(-10, W + 40, step):
            cv.ellipse([x + off - 8, y - 8, x + off + 8, y + 8], fill=pal["dot"])


def _frame(pal):
    """地・カード・ブランド行・ドメインまでの共通部分。カード内の文字領域(x0,x1)を返す。"""
    cv = OgCanvas(pal["bg"])
    _dots(cv, pal)
    x0, y0, x1, y1 = CARD
    cv.rrect([x0 + 14, y0 + 16, x1 + 14, y1 + 16], 40, fill=pal["deep"])
    cv.rrect(CARD, 40, fill=ic.WHITE, outline=ic.INK, width=5)
    ic.washi_tape(cv, x0 + 150, y0 + 2, pal["tape"], w=170, h=46, angle=-6)
    for x, y, r in ((x1 - 60, y0 + 70, 18), (x1 - 110, y0 + 120, 11), (x0 + 30, y1 - 120, 12)):
        ic.sparkle(cv, x, y, r, pal["mark"])
    return cv


def _brand(cv, pal, site):
    x, y = CARD[0] + 56, CARD[1] + 42
    ic.kokemaru(cv, x + 22, y + 26, 20)
    cv.text((x + 56, y + 6), site, ic.font("bold", 30), pal["deep"])


def _domain(cv, pal, domain):
    f = ic.font("bold", 24)
    w = cv.length(domain, f) + 48
    x, y = CARD[0] + 56, CARD[3] - 76
    cv.rrect([x, y, x + w, y + 44], 22, fill=pal["mark"])
    cv.text((x + w / 2, y + 22), domain, f, ic.INK, anchor="mm")


def _mascot(cv, pal, bubble=None):
    x1, y1 = CARD[2], CARD[3]
    ic.kokemaru(cv, x1 - 110, y1 - 52, 92)
    ic.heart(cv, x1 - 220, y1 - 160, 18, ic.BLUSH)
    ic.heart(cv, x1 - 248, y1 - 120, 11, ic.BLUSH)
    if bubble:  # こけまるの頭の上(タイトル列の右側の空き)に置く
        f = ic.font("bold", 26)
        w = cv.length(bubble, f) + 48
        bx, by = x1 - 28 - w, y1 - 318
        tx = x1 - 110
        cv.poly([(tx - 20, by + 56), (tx + 16, by + 56), (tx - 4, by + 88)], ic.INK)
        cv.rrect([bx, by, bx + w, by + 60], 30, fill=ic.WHITE, outline=ic.INK, width=4)
        cv.poly([(tx - 15, by + 54), (tx + 11, by + 54), (tx - 4, by + 78)], ic.WHITE)
        cv.text((bx + w / 2, by + 30), bubble, f, pal["deep"], anchor="mm")


_NO_LINE_END = set("「『（(【〈《“‘")


def _wrap(text, f, max_w):
    """ig_cards.wrap に行末禁則(開き括弧を次の行へ)を足したもの。"""
    lines = []
    for part in text.split("\n"):
        for ln in ic.wrap(part, f, max_w):
            if lines and lines[-1] and lines[-1][-1] in _NO_LINE_END:
                ln = lines[-1][-1] + ln
                lines[-1] = lines[-1][:-1]
            lines.append(ln)
    return [l for l in lines if l]


def _ellipsize(cv, text, f, max_w):
    lines = ic.wrap(text, f, max_w)
    if len(lines) == 1:
        return lines[0]
    last = lines[0]
    while last and cv.length(last + "…", f) > max_w:
        last = last[:-1]
    return last + "…"


def _title(cv, pal, text, x, y, max_w, bottom, sizes):
    """縦横に収まる最大の級数でタイトルを組み、行ごとに蛍光ペンを引く。最後の y を返す。"""
    chosen = None
    for size in sizes:
        f = ic.font("bold", size)
        lines = _wrap(text, f, max_w)
        lh = size * 1.34
        fits = y + lh * len(lines) <= bottom
        orphan = len(lines) > 1 and len(lines[-1]) <= 2  # 最終行が1〜2文字だけになるのを避ける
        if fits and not orphan:
            chosen = (f, lines, lh)
            break
        if fits and chosen is None:
            chosen = (f, lines, lh)
    if chosen is None:
        chosen = (f, lines, lh)
    f, lines, lh = chosen
    max_lines = max(1, int((bottom - y) // lh))
    if len(lines) > max_lines:  # 下限でも溢れるときは末尾を「…」に
        lines = lines[:max_lines]
        last = lines[-1]
        while last and cv.length(last + "…", f) > max_w:
            last = last[:-1]
        lines[-1] = last + "…"
    return cv.marker(x, y, lines, f, ic.INK, pal["mark"], leading=1.34)


def section(title, desc, pal_key, site, domain, bubble=None):
    """セクションの OGP。title は "\\n" で改行指定できる。"""
    pal = PALETTES[pal_key]
    cv = _frame(pal)
    _brand(cv, pal, site)
    x = CARD[0] + 56
    max_w = CARD[2] - x - 270
    y = _title(cv, pal, title, x, CARD[1] + 130, max_w, CARD[3] - 160, (78, 70, 62, 54))
    if desc:
        f = ic.font("regular", 26)
        cv.text((x, y + 14), _ellipsize(cv, desc, f, max_w), f, ic.INK_SOFT)
    _domain(cv, pal, domain)
    _mascot(cv, pal, bubble)
    return cv.done()


def article(title, tag, desc, pal_key, site, domain):
    """ブログ記事の OGP(一覧カードのサムネも兼ねる)。タイトルが主役。"""
    pal = PALETTES[pal_key]
    cv = _frame(pal)
    _brand(cv, pal, site)
    x = CARD[0] + 56
    y = CARD[1] + 112
    if tag:
        w, h = ic.pill(cv, x, y, tag, ic.WHITE, pal["accent"], size=26, outline=ic.INK)
        y += h + 26
    max_w = CARD[2] - x - 230
    y = _title(cv, pal, title, x, y, max_w, CARD[3] - 96, (62, 56, 50, 44, 40))
    if desc and CARD[3] - 96 - y >= 46:
        f = ic.font("regular", 24)
        cv.text((x, y + 10), _ellipsize(cv, desc, f, max_w - 40), f, ic.INK_SOFT)
    _domain(cv, pal, domain)
    _mascot(cv, pal)
    return cv.done()
