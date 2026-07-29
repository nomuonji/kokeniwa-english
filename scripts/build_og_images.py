# -*- coding: utf-8 -*-
"""OGP画像(1200x630 PNG)を site/static/og/ に生成する。

SNSでシェアされたときのカードに出る画像。サイトの「苔むす庭」の世界観
(生成りの和紙・墨・苔緑)をそのまま持ち込み、遠山→苔石→灯籠のシルエットを
Pillowで描いている(サイト背景の garden SVG のラスタ版)。

使い方:
    python scripts/build_og_images.py        # 全ページ分を再生成

生成物は git にコミットする(Cloudflare Pages は dist をそのまま配信し、
ビルド時に Pillow を動かさないため)。フォントは Windows 同梱の Noto(OFL)。
セクションを増やすときは SECTIONS に1行足すだけでよい。
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "site" / "static" / "og"

W, H = 1200, 630
FONT_DIR = Path("C:/Windows/Fonts")
SERIF = FONT_DIR / "NotoSerifJP-VF.ttf"
SANS = FONT_DIR / "NotoSansJP-VF.ttf"

# style.css のライトテーマ変数と合わせる
BG = (243, 241, 231)        # --bg 生成り
BG_TOP = (250, 249, 242)
TEXT = (35, 40, 31)         # --text 墨
MUTED = (103, 112, 93)      # --text-muted
GARDEN_FAR = (231, 233, 216)
GARDEN_MID = (218, 224, 198)
GARDEN_NEAR = (201, 210, 172)
STONE = (205, 200, 181)
LANTERN = (183, 177, 157)
LIGHT = (230, 180, 95)
MOSS = (139, 166, 86)
MOSS2 = (159, 185, 106)

PRIMARY = (77, 106, 56)     # 苔緑
USCPA = (47, 115, 104)      # 水
LEGAL = (150, 100, 42)      # 土

SITE = "Kokeniwa English"
DOMAIN = "en.kokeniwa.net"

# slug: (見出し, 説明, アクセント色)  ※見出しは "\n" で改行
SECTIONS = {
    "default": ("苔むすように、\n言葉を育てる。",
                "英文解釈・USCPA・法律・一般英単語を無料で。毎日すこしずつ。", PRIMARY),
    "reading": ("英文解釈\nトレーニング",
                "構文・語法・論理の急所を突く全200問。全文訳つき・無料。", PRIMARY),
    "uscpa": ("USCPA英単語\n1000語",
              "FAR・AUD・REGなど科目別フラッシュカード。無料・登録不要。", USCPA),
    "legal": ("法律英単語\n1000語",
              "契約・会社法・訴訟など10分野。分野別フラッシュカード。", LEGAL),
    "training": ("英単語\nトレーニング",
                 "英検準1級・ニュース・ドラマ・句動詞・イディオム 全2920語。", PRIMARY),
    "books": ("Kindle教材\n全6冊",
              "英語トレーニングシリーズ＋名作で学ぶ英語多読シリーズ。KU対象。", LEGAL),
    "blog": ("ブログ",
             "英語学習の続け方、精読と多読、教材の使い方。", USCPA),
    "sns": ("SNSで毎日配信中",
            "英文解釈・USCPA・法律・一般英単語の4アカウントをThreadsで。", PRIMARY),
}


def font(path, size, weight="Regular"):
    f = ImageFont.truetype(str(path), size)
    try:
        f.set_variation_by_name(weight)
    except OSError:  # 可変フォントでない環境向けのフォールバック
        pass
    return f


def vgradient(img, top, bottom):
    """上から下への薄いグラデーション(和紙のむら)。"""
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)],
               fill=tuple(round(a + (b - a) * t) for a, b in zip(top, bottom)))


def hill(d, points, color):
    """下端まで塗りつぶす丘のシルエット。points=[(x,y), ...]"""
    d.polygon(points + [(W, H), (0, H)], fill=color)


def wave(y0, amp, phase=0.0, step=24):
    """ゆるい波形の稜線を作る。"""
    import math
    pts = []
    for x in range(0, W + step, step):
        t = x / W
        y = y0 + amp * math.sin(t * 3.1 + phase) + amp * 0.4 * math.sin(t * 7.3 + phase)
        pts.append((x, y))
    return pts


def moss_cap(d, cx, cy, rx, sizes):
    """石を覆うもこもこの苔。円を横に並べる。"""
    n = len(sizes)
    for i, r in enumerate(sizes):
        x = cx - rx + (2 * rx) * (i / (n - 1) if n > 1 else 0.5)
        d.ellipse([x - r, cy - r, x + r, cy + r], fill=MOSS)
    for i, r in enumerate(sizes[1:-1], start=1):
        x = cx - rx * 0.6 + (1.2 * rx) * ((i - 1) / max(n - 3, 1))
        rr = r * 0.5
        d.ellipse([x - rr, cy - r * 0.7 - rr, x + rr, cy - r * 0.7 + rr], fill=MOSS2)


def lantern(d, x, y, s=1.0):
    """石灯籠。x,y は台座の中心。"""
    def rect(x0, y0, w, h, fill=LANTERN):
        d.rectangle([x + x0 * s, y + y0 * s, x + (x0 + w) * s, y + (y0 + h) * s], fill=fill)

    def poly(pts, fill=LANTERN):
        d.polygon([(x + px * s, y + py * s) for px, py in pts], fill=fill)

    rect(-27, 0, 54, 18)              # 台座
    rect(-9, -58, 18, 58)             # 竿
    poly([(-19, -58), (19, -58), (12, -73), (-12, -73)])   # 中台
    rect(-19, -105, 38, 33)           # 火袋
    r = 8.5 * s
    cx, cy = x, y - 89 * s
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=LIGHT)   # 灯
    poly([(-29, -105), (29, -105), (13, -123), (-13, -123)])  # 笠
    poly([(-10, -123), (10, -123), (0, -134)])                # 宝珠台
    rr = 5 * s
    cx2, cy2 = x, y - 139 * s
    d.ellipse([cx2 - rr, cy2 - rr, cx2 + rr, cy2 + rr], fill=LANTERN)


def rake_lines(d):
    """枯山水の砂紋。手前の地面にゆるい同心の弧を引く。"""
    for i in range(4):
        box = [-120 + i * -30, 590 + i * 14, 640 + i * 40, 734 + i * 30]
        d.arc(box, start=200, end=340, fill=(207, 211, 189), width=3)


def draw_garden(img):
    d = ImageDraw.Draw(img)
    hill(d, wave(430, 16, 0.4), GARDEN_FAR)
    hill(d, wave(492, 12, 2.1), GARDEN_MID)
    hill(d, wave(556, 8, 4.0), GARDEN_NEAR)
    rake_lines(d)
    # 石＋苔
    d.ellipse([700, 520, 940, 610], fill=STONE)
    moss_cap(d, 820, 528, 108, [22, 27, 30, 27, 22])
    d.ellipse([948, 546, 1088, 604], fill=STONE)
    moss_cap(d, 1018, 552, 62, [15, 19, 21, 19, 15])
    lantern(d, 1120, 566, 0.72)
    # 小さな苔山(左)
    moss_cap(d, 250, 588, 46, [12, 16, 18, 16, 12])
    moss_cap(d, 430, 596, 36, [10, 13, 15, 13, 10])


def draw_brand(d):
    """左上のブランド行(本のマーク + サイト名)。"""
    x, y = 72, 66
    d.rounded_rectangle([x, y, x + 34, y + 42], radius=5, outline=PRIMARY, width=3)
    d.line([x + 8, y + 13, x + 26, y + 13], fill=PRIMARY, width=3)
    d.line([x + 8, y + 23, x + 21, y + 23], fill=PRIMARY, width=3)
    d.text((x + 50, y + 6), SITE, font=font(SANS, 30, "Bold"), fill=PRIMARY)


def build(slug, title, desc, accent):
    img = Image.new("RGB", (W, H), BG)
    vgradient(img, BG_TOP, BG)
    draw_garden(img)
    d = ImageDraw.Draw(img)

    draw_brand(d)
    # アクセントの縦線（セクションの色）
    d.rounded_rectangle([72, 168, 79, 168 + 52 * len(title.split("\n"))],
                        radius=4, fill=accent)

    f_title = font(SERIF, 76, "Bold")
    y = 158
    for line in title.split("\n"):
        d.text((104, y), line, font=f_title, fill=TEXT)
        y += 96
    d.text((104, y + 34), desc, font=font(SANS, 27), fill=MUTED)

    # 左下にドメイン（右下は灯籠・苔石と重なるため）
    d.text((104, H - 76), DOMAIN, font=font(SANS, 26, "Medium"), fill=MUTED)
    # 下端のアクセントライン
    d.rectangle([0, H - 8, W, H], fill=accent)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{slug}.png"
    img.save(path, optimize=True)
    return path


def build_touch_icon():
    """iOSのホーム画面用アイコン(180x180 PNG)。favicon.svg と同じ意匠。"""
    s = 12  # favicon.svg の 64x64 座標系を12倍で描いて180pxへ縮小(=アンチエイリアス)
    img = Image.new("RGB", (64 * s, 64 * s), PRIMARY)
    d = ImageDraw.Draw(img)
    ink = (251, 250, 243)
    w = 4 * s

    def pts(*xy):
        return [(x * s, y * s) for x, y in xy]

    # 本の輪郭＋背(favicon.svg と同じ形)
    d.line(pts((14, 16), (20, 10), (50, 10), (50, 48), (20, 48), (14, 54), (14, 16)),
           fill=ink, width=w, joint="curve")
    # 本文の2本線
    d.line(pts((24, 22), (42, 22)), fill=ink, width=w)
    d.line(pts((24, 30), (36, 30)), fill=ink, width=w)
    img = img.resize((180, 180), Image.LANCZOS)
    path = OUT_DIR.parent / "apple-touch-icon.png"
    img.save(path, optimize=True)
    print(f"icon: {path.relative_to(ROOT)} ({path.stat().st_size // 1024} KB)")


def main():
    which = sys.argv[1:] or list(SECTIONS) + ["icon"]
    if "icon" in which:
        build_touch_icon()
        which = [w for w in which if w != "icon"]
    for slug in which:
        if slug not in SECTIONS:
            print(f"未知のセクション: {slug}")
            continue
        p = build(slug, *SECTIONS[slug])
        print(f"{slug}: {p.relative_to(ROOT)} ({p.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
