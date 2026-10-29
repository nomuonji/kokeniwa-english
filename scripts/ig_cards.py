# -*- coding: utf-8 -*-
"""Instagram 用カルーセル画像(1080x1350 JPEG)を Threads 投稿と同じ中身から作る。

Threads の自動投稿(auto_post.py)が選んだ「今回の分」(build_current の戻り値)を
そのまま受け取り、スワイプして読む「ステッカー帳」風のカードに組み直す。

デザインの方針(Instagram はサイトや Threads と違う、保存したくなる可愛さ):
  - シリーズごとにパステルの色と水玉の背景を変えて、一覧で見分けがつくように
  - 白いカードは太めの縁取り＋ずらした影でステッカー風、上にマスキングテープ
  - 丸ゴシック(M PLUS Rounded 1c)、意味は蛍光ペンを引いたように
  - マスコットの「こけまる」(苔玉)がカードの端からのぞく

  単語系(vocab / training) : 表紙(今回の語の一覧) → 1語1枚(意味・例文) → 締め
  英文解釈(reading)         : 問題 → 正解と全文訳 → 解説 → 締め

使い方(プレビュー):
    python scripts/ig_cards.py uscpa --cursor 0 --out out/ig
    python scripts/ig_cards.py training:news --cursor 0 --out out/ig
    python scripts/ig_cards.py reading --id 1 --out out/ig

フォント: fonts/ に M PLUS Rounded 1c(OFL)を置く(ワークフローが実行時に取得する。
リポジトリには入れない)。無ければ Noto Sans CJK で代用する。
    python scripts/ig_cards.py --fetch-fonts   # ローカルで取得
"""
import argparse
import math
import random
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "fonts"
W, H = 1080, 1350          # Instagram 推奨の縦長 4:5
SS = 2                     # 2倍で描いて縮小(角丸や円をなめらかに)

INK = (64, 54, 66)
INK_SOFT = (122, 110, 124)
WHITE = (255, 253, 250)
MOSS = (128, 178, 96)
MOSS_LIGHT = (166, 207, 128)
MOSS_DARK = (88, 132, 66)
BLUSH = (255, 160, 170)

SITE = "Kokeniwa English"
DOMAIN = "en.kokeniwa.net"

# シリーズごとの色(背景・アクセント・影・蛍光ペン)と表示名
SERIES = {
    "uscpa": {"label": "USCPA英単語", "bg": (220, 243, 236), "dot": (200, 233, 223),
              "accent": (52, 168, 146), "deep": (36, 112, 99), "mark": (176, 236, 218),
              "tape": (255, 214, 120)},
    "legal": {"label": "法律英単語", "bg": (254, 236, 224), "dot": (250, 220, 203),
              "accent": (232, 128, 88), "deep": (166, 82, 52), "mark": (255, 208, 182),
              "tape": (150, 210, 200)},
    "training": {"label": "こつこつ英単語", "bg": (255, 245, 206), "dot": (252, 234, 178),
                 "accent": (232, 160, 30), "deep": (160, 104, 18), "mark": (255, 226, 130),
                 "tape": (246, 170, 190)},
    "reading": {"label": "英文解釈トレーニング", "bg": (236, 232, 252), "dot": (222, 215, 248),
                "accent": (132, 110, 214), "deep": (86, 66, 160), "mark": (218, 208, 252),
                "tape": (255, 200, 140)},
}

# 画面の文言(JP 版はここを英語に差し替える)
TEXT = {
    "cover_title": "今日の{n}語",
    "cover_hint": "めくって例文もチェック →",
    "example": "例文",
    "close_lead": "保存して\nあとで見返してね",
    "close_body_words": "全{total}語の単語帳・フラッシュカードを\n無料で公開中",
    "close_body_reading": "英文・設問・全文訳つきの問題を\n全{total}問 無料で公開中",
    "close_button": "プロフィールのリンクから",
    "close_threads": "Threadsでも毎日配信中 {handle}",
    "bubble_close": "ほぞんしてね!",
    "bubble_cover": "きょうも\nこつこつ!",
    "q_label": "Q",
    "q_hint": "考えたらめくってね →",
    "answer": "こたえ",
    "translation": "全文訳",
    "explanation": "解説のポイント",
    "point": "ポイント",
}

# --- フォント -------------------------------------------------------------

FONT_URLS = {
    "MPLUSRounded1c-Medium.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/mplusrounded1c/MPLUSRounded1c-Medium.ttf",
    "MPLUSRounded1c-ExtraBold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/mplusrounded1c/MPLUSRounded1c-ExtraBold.ttf",
}
_CANDIDATES = {
    "regular": [(FONT_DIR / "MPLUSRounded1c-Medium.ttf", None),
                (Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"), 0),
                (Path("C:/Windows/Fonts/NotoSansJP-VF.ttf"), None)],
    "bold": [(FONT_DIR / "MPLUSRounded1c-ExtraBold.ttf", None),
             (Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"), 0),
             (Path("C:/Windows/Fonts/NotoSansJP-VF.ttf"), None)],
}
_cache = {}


def fetch_fonts():
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    for name, url in FONT_URLS.items():
        dst = FONT_DIR / name
        if not dst.exists():
            urllib.request.urlretrieve(url, dst)
            print(f"downloaded {dst}")


def font(weight, size):
    """weight: regular / bold。size は仕上がり px(内部で SS 倍)。"""
    key = (weight, size)
    if key not in _cache:
        for path, idx in _CANDIDATES[weight]:
            if path.exists():
                _cache[key] = (ImageFont.truetype(str(path), size * SS, index=idx)
                               if idx is not None else ImageFont.truetype(str(path), size * SS))
                break
        else:
            raise FileNotFoundError("フォントが見つかりません(--fetch-fonts か fonts-noto-cjk)")
    return _cache[key]


# --- 文字組み -------------------------------------------------------------

_NO_LINE_START = set("、。，．・：；？！ー)）」』】〕〉》’”%％…ぁぃぅぇぉっゃゅょ")


def _tokens(text):
    out, buf = [], ""
    for ch in text:
        if ord(ch) > 0x2E7F:
            if buf:
                out.append(buf)
                buf = ""
            out.append(ch)
        elif ch == " ":
            out.append(buf + ch)
            buf = ""
        else:
            buf += ch
    if buf:
        out.append(buf)
    return out


def wrap(text, f, width):
    width *= SS
    lines = []
    for para in str(text).split("\n"):
        line = ""
        for tok in _tokens(para):
            if f.getlength(line + tok.rstrip()) <= width or not line.strip():
                line += tok
            elif tok[0] in _NO_LINE_START:
                line += tok
            else:
                lines.append(line.rstrip())
                line = tok.lstrip()
        lines.append(line.rstrip())
    return lines


def fit(text, weight, width, max_size, min_size, max_lines):
    size = max_size
    while True:
        f = font(weight, size)
        lines = wrap(text, f, width)
        if len(lines) <= max_lines or size <= min_size:
            return f, lines
        size -= 3


class Canvas:
    """SS 倍の内部座標を隠して、仕上がり px で描く小さなラッパー。"""

    def __init__(self, bg):
        self.img = Image.new("RGB", (W * SS, H * SS), bg)
        self.d = ImageDraw.Draw(self.img, "RGBA")

    @staticmethod
    def s(v):
        return [round(x * SS) for x in v] if isinstance(v, (list, tuple)) else round(v * SS)

    def rrect(self, box, r, fill=None, outline=None, width=0):
        self.d.rounded_rectangle(self.s(box), radius=self.s(r), fill=fill, outline=outline, width=self.s(width))

    def ellipse(self, box, fill=None, outline=None, width=0):
        self.d.ellipse(self.s(box), fill=fill, outline=outline, width=self.s(width))

    def poly(self, pts, fill):
        self.d.polygon([(x * SS, y * SS) for x, y in pts], fill=fill)

    def line(self, pts, fill, width):
        self.d.line([(x * SS, y * SS) for x, y in pts], fill=fill, width=self.s(width), joint="curve")

    def text(self, xy, s, f, fill, anchor="la"):
        self.d.text((xy[0] * SS, xy[1] * SS), s, font=f, fill=fill, anchor=anchor)

    def length(self, s, f):
        return f.getlength(s) / SS

    def lines(self, x, y, lines, f, fill, leading=1.5, anchor="la"):
        step = f.size / SS * leading
        for ln in lines:
            self.text((x, y), ln, f, fill, anchor)
            y += step
        return y

    def marker(self, x, y, lines, f, fill, mark, leading=1.4):
        """蛍光ペンを引いた行(文字の下半分に色の帯)。"""
        step = f.size / SS * leading
        for ln in lines:
            w = self.length(ln, f)
            fs = f.size / SS
            self.rrect([x - 10, y + fs * 0.55, x + w + 10, y + fs * 1.18], 12, fill=mark)
            self.text((x, y), ln, f, fill)
            y += step
        return y

    def done(self):
        return self.img.resize((W, H), Image.LANCZOS)


# --- 飾り -------------------------------------------------------------------

def dots_bg(cv, pal, seed):
    """水玉の背景＋ところどころ小さなキラキラ。"""
    step = 72
    for row, y in enumerate(range(-20, H + 40, step)):
        off = step / 2 if row % 2 else 0
        for x in range(-20, W + 40, step):
            r = 9
            cv.ellipse([x + off - r, y - r, x + off + r, y + r], fill=pal["dot"])
    rnd = random.Random(seed)
    for _ in range(5):
        sparkle(cv, rnd.uniform(60, W - 60), rnd.uniform(60, H - 60), rnd.uniform(12, 22), WHITE)


def sparkle(cv, cx, cy, r, color):
    """4方向に伸びるキラキラ。"""
    k = r * 0.28
    cv.poly([(cx, cy - r), (cx + k, cy - k), (cx + r, cy), (cx + k, cy + k),
             (cx, cy + r), (cx - k, cy + k), (cx - r, cy), (cx - k, cy - k)], color)


def heart(cv, cx, cy, s, color):
    cv.ellipse([cx - s, cy - s * 0.7, cx, cy + s * 0.3], fill=color)
    cv.ellipse([cx, cy - s * 0.7, cx + s, cy + s * 0.3], fill=color)
    cv.poly([(cx - s * 0.96, cy - s * 0.05), (cx + s * 0.96, cy - s * 0.05), (cx, cy + s)], color)


def sticker_card(cv, box, pal, r=46, tape=True):
    """太い縁取りとずらした影のステッカー風カード。"""
    x0, y0, x1, y1 = box
    cv.rrect([x0 + 14, y0 + 16, x1 + 14, y1 + 16], r, fill=pal["deep"])
    cv.rrect(box, r, fill=WHITE, outline=INK, width=5)
    if tape:
        washi_tape(cv, (x0 + x1) / 2, y0 + 2, pal["tape"])


def washi_tape(cv, cx, cy, color, w=190, h=54, angle=-4):
    layer = Image.new("RGBA", (w * SS, h * SS), color + (215,))
    d = ImageDraw.Draw(layer)
    for i in range(0, w * SS, 26 * SS):  # ストライプ
        d.rectangle([i, 0, i + 11 * SS, h * SS], fill=(255, 255, 255, 70))
    layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    cv.img.paste(layer, (round(cx * SS - layer.width / 2), round(cy * SS - layer.height / 2)), layer)


def kokemaru(cv, cx, cy, r, mood="smile", flip=False):
    """マスコット「こけまる」(苔玉)。cx,cy=中心、r=半径。"""
    # 影
    cv.ellipse([cx - r * 0.85, cy + r * 0.82, cx + r * 0.85, cy + r * 1.08], fill=(0, 0, 0, 28))
    # 体(もこもこの縁)
    for i in range(14):
        a = i / 14 * math.tau
        bx, by = cx + math.cos(a) * r * 0.86, cy + math.sin(a) * r * 0.86
        cv.ellipse([bx - r * 0.24, by - r * 0.24, bx + r * 0.24, by + r * 0.24], fill=MOSS)
    cv.ellipse([cx - r * 0.95, cy - r * 0.95, cx + r * 0.95, cy + r * 0.95], fill=MOSS)
    for dx, dy, rr in ((-0.45, -0.5, 0.2), (0.35, -0.6, 0.15), (0.55, 0.2, 0.13), (-0.6, 0.25, 0.12)):
        cv.ellipse([cx + (dx - rr) * r, cy + (dy - rr) * r, cx + (dx + rr) * r, cy + (dy + rr) * r],
                   fill=MOSS_LIGHT)
    # 芽
    sx = cx + (r * 0.15 if not flip else -r * 0.15)
    cv.line([(sx, cy - r * 0.92), (sx, cy - r * 1.28)], MOSS_DARK, max(3, r * 0.07))
    cv.ellipse([sx - r * 0.34, cy - r * 1.45, sx, cy - r * 1.22], fill=MOSS_LIGHT)
    cv.ellipse([sx, cy - r * 1.52, sx + r * 0.34, cy - r * 1.27], fill=MOSS_LIGHT)
    # 顔
    ex = r * 0.3
    ey = cy + r * 0.02
    er = r * 0.09
    for sgn in (-1, 1):
        cv.ellipse([cx + sgn * ex - er, ey - er * 1.3, cx + sgn * ex + er, ey + er * 1.3], fill=INK)
        cv.ellipse([cx + sgn * ex - er * 0.2, ey - er * 0.9, cx + sgn * ex + er * 0.5, ey - er * 0.2],
                   fill=WHITE)
        cv.ellipse([cx + sgn * r * 0.52 - r * 0.13, ey + r * 0.16, cx + sgn * r * 0.52 + r * 0.13,
                    ey + r * 0.28], fill=BLUSH + (200,))
    if mood == "open":
        cv.ellipse([cx - r * 0.1, ey + r * 0.14, cx + r * 0.1, ey + r * 0.34], fill=(200, 80, 90))
    else:
        cv.d.arc(cv.s([cx - r * 0.12, ey + r * 0.06, cx + r * 0.12, ey + r * 0.28]), 20, 160,
                 fill=INK, width=cv.s(max(3, r * 0.05)))


def bubble(cv, x, y, text, pal, tail="left", size=34):
    """吹き出し。x,y は左上。"""
    f = font("bold", size)
    lines = text.split("\n")
    w = max(cv.length(l, f) for l in lines) + 56
    h = len(lines) * size * 1.35 + 34
    tx = x + 46 if tail == "left" else x + w - 46
    cv.poly([(tx - 18, y + h - 4), (tx + 18, y + h - 4), (tx + (-26 if tail == "left" else 26), y + h + 34)], INK)
    cv.rrect([x, y, x + w, y + h], 30, fill=WHITE, outline=INK, width=4)
    cv.poly([(tx - 13, y + h - 6), (tx + 13, y + h - 6), (tx + (-20 if tail == "left" else 20), y + h + 24)], WHITE)
    cv.lines(x + w / 2, y + 17, lines, f, pal["deep"], leading=1.35, anchor="ma")
    return w, h


def pill(cv, x, y, text, fg, bg, size=30, pad=26, outline=None):
    f = font("bold", size)
    w = cv.length(text, f) + pad * 2
    h = size * 1.75
    cv.rrect([x, y, x + w, y + h], h / 2, fill=bg, outline=outline, width=4 if outline else 0)
    cv.text((x + w / 2, y + h / 2), text, f, fg, anchor="mm")
    return w, h


def num_badge(cv, cx, cy, n, pal, r=34):
    cv.ellipse([cx - r, cy - r, cx + r, cy + r], fill=pal["accent"], outline=INK, width=4)
    cv.text((cx, cy + 1), str(n), font("bold", round(r * 1.05)), WHITE, anchor="mm")


def header(cv, pal, sub):
    w, _ = pill(cv, 70, 58, pal["label"], WHITE, pal["accent"], size=32, outline=INK)
    if sub:
        pill(cv, W - 70 - cv.length(sub, font("bold", 28)) - 48, 62, sub, INK, WHITE, size=28, pad=24, outline=INK)


def page_dots(cv, page, total, pal):
    gap = 30
    x = W / 2 - gap * (total - 1) / 2
    for i in range(total):
        r = 11 if i + 1 == page else 7
        fill = pal["accent"] if i + 1 == page else WHITE
        cv.ellipse([x - r, H - 58 - r, x + r, H - 58 + r], fill=fill, outline=INK, width=3)
        x += gap


def place(cv, top, bottom, draw_fn, bias=0.45):
    """draw_fn(cv) で透明レイヤに y=0 から描き、top〜bottom の間に縦方向で置く。"""
    layer = Canvas((0, 0, 0))
    layer.img = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    layer.d = ImageDraw.Draw(layer.img, "RGBA")
    draw_fn(layer)
    bbox = layer.img.getbbox()
    if not bbox:
        return
    h = (bbox[3] - bbox[1]) / SS
    y = top + max(0, (bottom - top - h) * bias) - bbox[1] / SS
    cv.img.paste(layer.img, (0, round(y * SS)), layer.img)


# --- 単語系 ---------------------------------------------------------------

CARD = [64, 170, W - 64, H - 150]   # 白カードの位置
IN_X = CARD[0] + 60                  # カード内の左端
IN_W = CARD[2] - CARD[0] - 120       # カード内の幅


def _base(pal, sub, seed):
    cv = Canvas(pal["bg"])
    dots_bg(cv, pal, seed)
    header(cv, pal, sub)
    sticker_card(cv, CARD, pal)
    return cv


def _word_cover(rows, pal, sub, title):
    cv = _base(pal, sub, 1)
    step = 132 if len(rows) <= 5 else 112

    def body(c):
        c.text((W / 2, 0), title, font("bold", 84), INK, anchor="ma")
        y = 140
        for i, r in enumerate(rows, 1):
            num_badge(c, IN_X + 30, y + 34, i, pal, r=30)
            f_t, t = fit(r["term"], "bold", IN_W - 90, 50 if step > 120 else 44, 30, 1)
            c.text((IN_X + 84, y), t[0], f_t, INK)
            sub_txt = f"{r['reading']}  {r['meaning']}" if r.get("reading") else r["meaning"]
            f_m, m = fit(sub_txt, "regular", IN_W - 90, 32, 22, 1)
            c.text((IN_X + 86, y + (64 if step > 120 else 56)), m[0], f_m, INK_SOFT)
            y += step

    place(cv, CARD[1] + 70, CARD[3] - 150, body, bias=0.3)
    if len(rows) <= 5:  # 6語だと一覧と重なるので、吹き出しは5語以下のときだけ
        kokemaru(cv, CARD[2] - 110, CARD[3] - 70, 72)
        bubble(cv, CARD[2] - 400, CARD[3] - 200, TEXT["bubble_cover"], pal, tail="right", size=30)
    else:
        kokemaru(cv, CARD[2] - 70, CARD[3] - 30, 50, flip=True)
    pill(cv, IN_X - 6, CARD[3] - 92, TEXT["cover_hint"], pal["deep"], pal["mark"], size=26)
    return cv


def _word_card(i, n, r, pal, sub):
    cv = _base(pal, sub, 10 + i)

    def body(c):
        y = 0
        if r.get("tag"):
            _, h = pill(c, IN_X, y, r["tag"], pal["deep"], pal["mark"], size=28)
            y += h + 34
        f_t, t = fit(r["term"], "bold", IN_W, 118, 54, 2)
        y = c.lines(IN_X, y, t, f_t, INK, leading=1.22)
        if r.get("reading"):
            f_r, rl = fit(r["reading"], "regular", IN_W, 40, 26, 1)
            y = c.lines(IN_X, y + 4, rl, f_r, INK_SOFT, leading=1.4)
        y += 18
        f_m, m = fit(r["meaning"], "bold", IN_W, 58, 34, 2)
        y = c.marker(IN_X, y, m, f_m, pal["deep"], pal["mark"])
        if r.get("example"):
            y += 56
            pill(c, IN_X, y, TEXT["example"], WHITE, pal["accent"], size=26, pad=20)
            y += 74
            f_e, e = fit(r["example"], "regular", IN_W, 42, 30, 4)
            y = c.lines(IN_X, y, e, f_e, INK, leading=1.5)
            if r.get("example_sub"):
                f_j, j = fit(r["example_sub"], "regular", IN_W, 32, 24, 3)
                c.lines(IN_X, y + 8, j, f_j, INK_SOFT, leading=1.55)

    place(cv, CARD[1] + 80, CARD[3] - 120, body, bias=0.4)
    num_badge(cv, CARD[0] + 20, CARD[1] + 20, f"{i}", pal, r=40)
    kokemaru(cv, CARD[2] - 70, CARD[3] - 30, 50, flip=True)
    return cv


def _closing(pal, body_text, handle):
    cv = Canvas(pal["bg"])
    dots_bg(cv, pal, 99)
    header(cv, pal, None)
    sticker_card(cv, CARD, pal)

    def body(c):
        f = font("bold", 66)
        y = c.lines(W / 2, 0, TEXT["close_lead"].split("\n"), f, INK, leading=1.3, anchor="ma")
        f_b = font("regular", 34)
        y = c.lines(W / 2, y + 30, body_text.split("\n"), f_b, INK_SOFT, leading=1.55, anchor="ma")
        f_btn = font("bold", 36)
        bw = c.length(TEXT["close_button"], f_btn) + 100
        y += 46
        c.rrect([(W - bw) / 2 + 8, y + 10, (W + bw) / 2 + 8, y + 98], 44, fill=pal["deep"])
        c.rrect([(W - bw) / 2, y, (W + bw) / 2, y + 88], 44, fill=pal["accent"], outline=INK, width=4)
        c.text((W / 2, y + 44), TEXT["close_button"], f_btn, WHITE, anchor="mm")
        if handle:
            c.text((W / 2, y + 140), TEXT["close_threads"].format(handle=handle), font("regular", 30),
                   INK_SOFT, anchor="ma")

    place(cv, CARD[1] + 90, CARD[3] - 330, body, bias=0.35)
    kokemaru(cv, W / 2 + 40, CARD[3] - 150, 100, mood="open")
    bubble(cv, W / 2 - 360, CARD[3] - 330, TEXT["bubble_close"], pal, tail="right", size=34)
    for x, y, s in ((W / 2 + 190, CARD[3] - 250, 26), (W / 2 + 230, CARD[3] - 200, 16)):
        heart(cv, x, y, s, BLUSH)
    return cv


def word_slides(series, rows, number_label, total, handle=None, cover_title=None):
    """rows: [{"term","meaning","example","example_sub","tag","reading"?}]"""
    pal = SERIES[series]
    slides = [_word_cover(rows, pal, number_label, cover_title or TEXT["cover_title"].format(n=len(rows)))]
    slides += [_word_card(i, len(rows), r, pal, number_label) for i, r in enumerate(rows, 1)]
    slides.append(_closing(pal, TEXT["close_body_words"].format(total=total), handle))
    return slides, pal


# --- 英文解釈 -------------------------------------------------------------

def reading_slides(it, total, handle=None):
    pal = SERIES["reading"]
    sub = f"No.{it['id']}"
    slides = []

    # 1. 問題
    cv = _base(pal, sub, 21)

    def q(c):
        y = 0
        _, h = pill(c, IN_X, y, it.get("category", ""), pal["deep"], pal["mark"], size=28)
        if it.get("point"):
            c.text((IN_X + c.length(it.get("category", ""), font("bold", 28)) + 80, y + 14),
                   f"{TEXT['point']}: {it['point']}", font("regular", 26), INK_SOFT)
        y += h + 40
        f_s, s = fit(it["sentence_en"], "bold", IN_W, 50, 32, 7)
        y = c.lines(IN_X, y, s, f_s, INK, leading=1.5) + 40
        c.ellipse([IN_X, y, IN_X + 64, y + 64], fill=pal["accent"], outline=INK, width=4)
        c.text((IN_X + 32, y + 33), TEXT["q_label"], font("bold", 36), WHITE, anchor="mm")
        f_q, ql = fit(it["question_ja"], "bold", IN_W - 90, 40, 28, 2)
        y = c.lines(IN_X + 88, y + 8, ql, f_q, pal["deep"], leading=1.4) + 14
        for i, ch in enumerate(it.get("choices") or []):
            f_c, cl = fit(ch, "regular", IN_W - 90, 36, 26, 1)
            c.rrect([IN_X, y, IN_X + IN_W, y + 66], 33, fill=pal["bg"], outline=INK, width=3)
            c.text((IN_X + 36, y + 33), "ABCD"[i], font("bold", 30), pal["deep"], anchor="mm")
            c.text((IN_X + 74, y + 33), cl[0], f_c, INK, anchor="lm")
            y += 82

    place(cv, CARD[1] + 80, CARD[3] - 130, q, bias=0.35)
    hint_w = cv.length(TEXT["q_hint"], font("bold", 26)) + 52
    pill(cv, CARD[2] - 50 - hint_w, CARD[3] - 96, TEXT["q_hint"], pal["deep"], pal["mark"], size=26)
    kokemaru(cv, CARD[0] + 70, CARD[3] - 30, 50)
    slides.append(cv)

    # 2. 正解と全文訳
    cv = _base(pal, sub, 22)

    def a(c):
        y = 0
        if it.get("format") == "quiz" and it.get("answer_index") is not None:
            pill(c, IN_X, y, TEXT["answer"], WHITE, pal["accent"], size=28)
            y += 80
            ans = f"{'ABCD'[it['answer_index']]}. {it['choices'][it['answer_index']]}"
            f_a, al = fit(ans, "bold", IN_W, 72, 40, 2)
            y = c.marker(IN_X, y, al, f_a, INK, pal["mark"]) + 50
        pill(c, IN_X, y, TEXT["translation"], WHITE, pal["accent"], size=28)
        y += 84
        f_t, tl = fit(it["translation_ja"], "regular", IN_W, 44, 30, 8)
        c.lines(IN_X, y, tl, f_t, INK, leading=1.65)

    place(cv, CARD[1] + 80, CARD[3] - 120, a, bias=0.4)
    kokemaru(cv, CARD[2] - 70, CARD[3] - 30, 50, flip=True)
    slides.append(cv)

    # 3. 解説
    cv = _base(pal, sub, 23)

    def e(c):
        pill(c, IN_X, 0, TEXT["explanation"], WHITE, pal["accent"], size=28)
        f_e, el = fit(it["explanation_ja"], "regular", IN_W, 40, 26, 13)
        c.lines(IN_X, 84, el, f_e, INK, leading=1.7)

    place(cv, CARD[1] + 80, CARD[3] - 120, e, bias=0.4)
    kokemaru(cv, CARD[2] - 70, CARD[3] - 30, 50, flip=True)
    slides.append(cv)

    slides.append(_closing(pal, TEXT["close_body_reading"].format(total=total), handle))
    return slides, pal


# --- 仕上げ -----------------------------------------------------------------

def finish(slides_pal):
    """ページ位置の点を入れて、仕上がりサイズの画像にする。"""
    slides, pal = slides_pal
    n = len(slides)
    out = []
    for i, cv in enumerate(slides, 1):
        page_dots(cv, i, n, pal)
        out.append(cv.done())
    return out


def save(slides, out_dir, prefix):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, img in enumerate(slides, 1):
        p = out_dir / f"{prefix}-{i:02d}.jpg"
        img.save(p, "JPEG", quality=90, optimize=True, progressive=True)
        paths.append(p)
    return paths


# --- auto_post.py から使う入口 ------------------------------------------------

def slides_for(acc, cur):
    """auto_post の build_current() の戻り値と、そのアカウント状態から画像を作る。"""
    handle = (acc.get("username") and f"@{acc['username']}") or None
    kind, meta = cur["kind"], cur["meta"]
    if kind == "reading":
        return finish(reading_slides(cur["item"], meta["total"], handle))
    rows = cur["rows"]
    series = "training" if kind == "training" else meta["set"]
    number = f"No.{rows[0]['id']}-{rows[-1]['id']}"
    return finish(word_slides(series, cur["card_rows"], number, meta["total"], handle,
                              cur.get("cover_title")))


def _cli():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    ap = argparse.ArgumentParser()
    ap.add_argument("what", nargs="?", help="uscpa / legal / training:<cat> / reading")
    ap.add_argument("--cursor", type=int, default=0)
    ap.add_argument("--id", type=int, default=1)
    ap.add_argument("--out", default="out/ig")
    ap.add_argument("--fetch-fonts", action="store_true")
    args = ap.parse_args()
    if args.fetch_fonts:
        fetch_fonts()
        if not args.what:
            return
    import auto_post as ap_mod  # 本番と同じ抽出ロジックを通す
    if args.what == "reading":
        items = sorted((it for _, it in ap_mod.reading.load_items() if it.get("status") != "rejected"),
                       key=lambda x: x["id"])
        idx = next(i for i, it in enumerate(items) if it["id"] == args.id)
        acc = {"content": "reading", "cursor": idx}
    elif args.what.startswith("training:"):
        cat = args.what.split(":", 1)[1]
        acc = {"content": "training", "rot_index": ap_mod.ftp.ROTATION.index(cat), "cursors": {cat: args.cursor}}
    else:
        acc = {"content": args.what, "cursor": args.cursor}
    cur = ap_mod.build_current(acc)
    for p in save(slides_for(acc, cur), args.out, args.what.replace(":", "-")):
        print(p)


if __name__ == "__main__":
    _cli()
