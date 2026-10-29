# -*- coding: utf-8 -*-
"""Instagram 用カルーセル画像(1080x1350 JPEG)を Threads 投稿と同じ中身から作る。

Threads の自動投稿(auto_post.py)が選んだ「今回の分」(build_current の戻り値)を
そのまま受け取り、サイトと同じ「苔むす庭」の世界観(生成りの和紙・墨・苔緑)で
スワイプして読むカードに組み直す。

  単語系(vocab / training) : 表紙(今回の語の一覧) → 1語1枚(意味・例文) → 締め
  英文解釈(reading)         : 問題 → 正解と全文訳 → 解説 → 締め

使い方(プレビュー):
    python scripts/ig_cards.py uscpa --cursor 0 --out out/ig
    python scripts/ig_cards.py training:news --cursor 0 --out out/ig
    python scripts/ig_cards.py reading --id 1 --out out/ig

フォントは Noto Sans/Serif CJK(Linux の fonts-noto-cjk、なければ Windows の Noto JP)。
"""
import argparse
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350          # Instagram 推奨の縦長 4:5
MARGIN = 96

# サイト(style.css / build_og_images.py)と同じ色
BG_TOP = (250, 249, 242)
BG = (243, 241, 231)
TEXT = (35, 40, 31)
MUTED = (103, 112, 93)
RULE = (214, 214, 196)
GARDEN_FAR = (231, 233, 216)
GARDEN_MID = (218, 224, 198)
GARDEN_NEAR = (201, 210, 172)
STONE = (205, 200, 181)
MOSS = (139, 166, 86)
MOSS2 = (159, 185, 106)
PAPER = (252, 251, 246)

PRIMARY = (77, 106, 56)
USCPA = (47, 115, 104)
LEGAL = (150, 100, 42)

SITE = "Kokeniwa English"
DOMAIN = "en.kokeniwa.net"

# Threads のアカウント種別ごとの見た目と文言
SERIES = {
    "uscpa": {"label": "USCPA英単語", "accent": USCPA},
    "legal": {"label": "法律英単語", "accent": LEGAL},
    "training": {"label": "こつこつ英単語", "accent": PRIMARY},
    "reading": {"label": "英文解釈トレーニング", "accent": PRIMARY},
}

# --- フォント -------------------------------------------------------------

_FONT_CANDIDATES = {
    ("sans", "regular"): [
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 0),
        ("/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc", 0),
        ("C:/Windows/Fonts/NotoSansJP-VF.ttf", None),
    ],
    ("sans", "bold"): [
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 0),
        ("/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc", 0),
        ("C:/Windows/Fonts/NotoSansJP-VF.ttf", "Bold"),
    ],
    ("serif", "bold"): [
        ("/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc", 0),
        ("/usr/share/fonts/noto-cjk/NotoSerifCJK-Bold.ttc", 0),
        ("C:/Windows/Fonts/NotoSerifJP-VF.ttf", "Bold"),
    ],
}
_font_cache = {}


def font(kind, weight, size):
    key = (kind, weight, size)
    if key in _font_cache:
        return _font_cache[key]
    for path, extra in _FONT_CANDIDATES[(kind, weight)]:
        if not Path(path).exists():
            continue
        if isinstance(extra, int):
            f = ImageFont.truetype(path, size, index=extra)
        else:
            f = ImageFont.truetype(path, size)
            if extra:
                try:
                    f.set_variation_by_name(extra)
                except OSError:
                    pass
        _font_cache[key] = f
        return f
    raise FileNotFoundError(
        "日本語フォントが見つかりません(Linux なら apt install fonts-noto-cjk)")


# --- 文字組み -------------------------------------------------------------

_NO_LINE_START = set("、。，．・：；？！ー)）」』】〕〉》’”%％…")


def _is_cjk(ch):
    return ord(ch) > 0x2E7F


def _tokens(text):
    """英単語はまとめて、和文は1文字ずつ区切る。"""
    out, buf = [], ""
    for ch in text:
        if _is_cjk(ch):
            if buf:
                out.append(buf)
                buf = ""
            out.append(ch)
        elif ch == " ":
            buf += ch
            out.append(buf)
            buf = ""
        else:
            buf += ch
    if buf:
        out.append(buf)
    return out


def wrap(text, f, width):
    """幅 width に収まるよう改行する(行頭禁則つき)。明示的な \\n も尊重する。"""
    lines = []
    for para in text.split("\n"):
        line = ""
        for tok in _tokens(para):
            if f.getlength(line + tok.rstrip()) <= width or not line.strip():
                line += tok
                continue
            if tok[0] in _NO_LINE_START and line:
                # 句読点を前の行へぶら下げる
                line += tok
                continue
            lines.append(line.rstrip())
            line = tok.lstrip()
        lines.append(line.rstrip())
    return lines


def fit(text, kind, weight, width, max_size, min_size, max_lines):
    """max_lines 行に収まる最大の文字サイズを探す。"""
    size = max_size
    while True:
        f = font(kind, weight, size)
        lines = wrap(text, f, width)
        if len(lines) <= max_lines or size <= min_size:
            return f, lines
        size -= 4


def draw_lines(d, xy, lines, f, fill, leading=1.5, anchor_x="left"):
    x, y = xy
    step = round(f.size * leading)
    for ln in lines:
        if anchor_x == "center":
            d.text((W / 2, y), ln, font=f, fill=fill, anchor="ma")
        else:
            d.text((x, y), ln, font=f, fill=fill)
        y += step
    return y


# --- 背景 -----------------------------------------------------------------

def _wave(y0, amp, phase, step=24):
    pts = []
    for x in range(0, W + step, step):
        t = x / W
        pts.append((x, y0 + amp * math.sin(t * 3.1 + phase) + amp * 0.4 * math.sin(t * 7.3 + phase)))
    return pts


def _hill(d, pts, color):
    d.polygon(pts + [(W, H), (0, H)], fill=color)


def _moss_stone(d, cx, cy, rx, ry):
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=STONE)
    n = 6
    for i in range(n):
        x = cx - rx * 0.85 + (1.7 * rx) * i / (n - 1)
        r = ry * (0.55 + 0.25 * math.sin(i * 1.7))
        d.ellipse([x - r, cy - ry * 0.75 - r, x + r, cy - ry * 0.75 + r], fill=MOSS)
    for i in range(n - 2):
        x = cx - rx * 0.55 + (1.1 * rx) * i / max(n - 3, 1)
        r = ry * 0.28
        d.ellipse([x - r, cy - ry * 1.15 - r, x + r, cy - ry * 1.15 + r], fill=MOSS2)


def background(garden_h=170):
    """和紙のグラデーション＋下端の庭。garden_h は庭の高さ。"""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(round(a + (b - a) * t) for a, b in zip(BG_TOP, BG)))
    base = H - garden_h
    _hill(d, _wave(base + 10, 18, 0.4), GARDEN_FAR)
    _hill(d, _wave(base + 60, 14, 1.9), GARDEN_MID)
    _moss_stone(d, W * 0.80, base + 110, 70, 30)
    _moss_stone(d, W * 0.17, base + 125, 46, 20)
    _hill(d, _wave(base + 120, 10, 3.0), GARDEN_NEAR)
    return img, d


def header(d, series_label, accent, sub):
    """左上: ●シリーズ名 / 右上: 番号など"""
    y = 78
    d.ellipse([MARGIN, y + 10, MARGIN + 18, y + 28], fill=accent)
    d.text((MARGIN + 32, y), series_label, font=font("sans", "bold", 32), fill=accent)
    if sub:
        d.text((W - MARGIN, y + 2), sub, font=font("sans", "regular", 28), fill=MUTED, anchor="ra")
    d.line([(MARGIN, y + 66), (W - MARGIN, y + 66)], fill=RULE, width=2)
    return y + 66


def footer(d, page, total, handle=None):
    y = H - 64
    left = f"{SITE} · {DOMAIN}"
    d.text((MARGIN, y), left, font=font("sans", "regular", 24), fill=MUTED)
    d.text((W - MARGIN, y), f"{page} / {total}", font=font("sans", "regular", 24), fill=MUTED, anchor="ra")


def swipe_hint(d, accent, text="スワイプ →"):
    d.text((W - MARGIN, H - 250), text, font=font("sans", "bold", 30), fill=accent, anchor="ra")


def centered(img, top, bottom, draw_fn, bias=0.42):
    """draw_fn(d) で透明レイヤに y=0 から描き、top〜bottom の間に縦方向で置く。

    bias<0.5 で少し上寄せ(視線の入りやすい位置)。はみ出すときは top 揃え。
    """
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer))
    bbox = layer.getbbox()
    if not bbox:
        return
    h = bbox[3] - bbox[1]
    room = bottom - top
    y = top + max(0, round((room - h) * bias)) - bbox[1]
    img.paste(layer, (0, y), layer)


def paper_panel(d, top, bottom):
    d.rounded_rectangle([MARGIN - 32, top, W - MARGIN + 32, bottom], radius=28, fill=PAPER, outline=RULE, width=2)


# --- 単語系 ---------------------------------------------------------------

def _word_cover(rows, label, accent, sub, cover_title):
    img, d = background()
    top = header(d, label, accent, sub)
    step = 150 if len(rows) <= 5 else 120

    def body(d):
        y = 0
        d.text((MARGIN, y), cover_title, font=font("serif", "bold", 80), fill=TEXT)
        y += 140
        paper_panel(d, y, y + 50 + len(rows) * step)
        y += 34
        for r in rows:
            f_t, t_lines = fit(r["term"], "sans", "bold", W - 2 * MARGIN, 54 if step >= 150 else 46, 32, 1)
            d.text((MARGIN, y), t_lines[0], font=f_t, fill=TEXT)
            f_m, m_lines = fit(r["meaning"], "sans", "regular", W - 2 * MARGIN, 36, 24, 1)
            d.text((MARGIN, y + (76 if step >= 150 else 66)), m_lines[0], font=f_m, fill=MUTED)
            y += step

    centered(img, top + 30, H - 290, body, bias=0.35)
    swipe_hint(d, accent, "1語ずつ例文つきで →")
    return img


def _word_card(r, label, accent, sub):
    img, d = background()
    top = header(d, label, accent, sub)
    inner = W - 2 * MARGIN

    def body(d):
        y = 0
        if r.get("tag"):
            tag_f = font("sans", "bold", 30)
            tw = tag_f.getlength(r["tag"]) + 44
            d.rounded_rectangle([MARGIN, y, MARGIN + tw, y + 54], radius=27, outline=accent, width=3)
            d.text((MARGIN + 22, y + 9), r["tag"], font=tag_f, fill=accent)
            y += 100
        f_t, t_lines = fit(r["term"], "serif", "bold", inner, 128, 60, 2)
        y = draw_lines(d, (MARGIN, y), t_lines, f_t, TEXT, leading=1.2)
        y += 20
        f_m, m_lines = fit(r["meaning"], "sans", "bold", inner, 60, 36, 2)
        y = draw_lines(d, (MARGIN, y), m_lines, f_m, accent, leading=1.35)
        if r.get("example_en"):
            y += 60
            d.line([(MARGIN, y), (MARGIN + 80, y)], fill=accent, width=4)
            y += 44
            f_e, e_lines = fit(r["example_en"], "sans", "regular", inner, 46, 32, 4)
            y = draw_lines(d, (MARGIN, y), e_lines, f_e, TEXT, leading=1.45)
            if r.get("example_ja"):
                y += 16
                f_j, j_lines = fit(r["example_ja"], "sans", "regular", inner, 36, 26, 3)
                draw_lines(d, (MARGIN, y), j_lines, f_j, MUTED, leading=1.55)

    centered(img, top + 40, H - 200, body)
    return img


def _closing(label, accent, lead, body, handle):
    img, d = background(garden_h=330)
    header(d, label, accent, None)
    y = 330
    f_l, l_lines = fit(lead, "serif", "bold", W - 2 * MARGIN, 72, 48, 3)
    y = draw_lines(d, (MARGIN, y), l_lines, f_l, TEXT, leading=1.35, anchor_x="center")
    y += 50
    f_b = font("sans", "regular", 36)
    y = draw_lines(d, (MARGIN, y), wrap(body, f_b, W - 2 * MARGIN), f_b, MUTED, leading=1.6, anchor_x="center")
    y += 60
    pill_f = font("sans", "bold", 34)
    text = "プロフィールのリンクから"
    pw = pill_f.getlength(text) + 80
    d.rounded_rectangle([(W - pw) / 2, y, (W + pw) / 2, y + 76], radius=38, fill=accent)
    d.text((W / 2, y + 18), text, font=pill_f, fill=PAPER, anchor="ma")
    y += 130
    if handle:
        d.text((W / 2, y), f"Threadsでも毎日配信中  {handle}", font=font("sans", "regular", 30), fill=MUTED, anchor="ma")
    return img


def word_slides(series, rows, number_label, total, handle=None, cover_title=None):
    """rows: [{"term","meaning","example_en","example_ja","tag"}]"""
    cfg = SERIES[series]
    label, accent = cfg["label"], cfg["accent"]
    slides = [_word_cover(rows, label, accent, number_label, cover_title or f"今日の{len(rows)}語")]
    slides += [_word_card(r, label, accent, number_label) for r in rows]
    slides.append(_closing(
        label, accent, "保存して、\nあとで見返そう。",
        f"全{total}語の無料単語帳・フラッシュカードは\n{DOMAIN} で公開中。", handle))
    return slides


# --- 英文解釈 -------------------------------------------------------------

def reading_slides(it, total, handle=None):
    cfg = SERIES["reading"]
    label, accent = cfg["label"], cfg["accent"]
    sub = f"No.{it['id']} · {it.get('category', '')}"
    inner = W - 2 * MARGIN
    slides = []

    # 1. 問題
    img, d = background()
    top = header(d, label, accent, sub)

    def q_body(d):
        y = 0
        if it.get("point"):
            d.text((MARGIN, y), f"ポイント：{it['point']}", font=font("sans", "regular", 30), fill=MUTED)
            y += 70
        f_s, s_lines = fit(it["sentence_en"], "serif", "bold", inner - 20, 58, 34, 7)
        ph = 60 + len(s_lines) * round(f_s.size * 1.5)
        paper_panel(d, y, y + ph)
        draw_lines(d, (MARGIN, y + 34), s_lines, f_s, TEXT, leading=1.5)
        y += ph + 60
        f_q, q_lines = fit(it["question_ja"], "sans", "bold", inner, 44, 32, 2)
        y = draw_lines(d, (MARGIN, y), q_lines, f_q, accent, leading=1.4)
        y += 14
        for i, c in enumerate(it.get("choices") or []):
            f_c, c_lines = fit(f"{'ABCD'[i]}. {c}", "sans", "regular", inner, 40, 28, 1)
            d.text((MARGIN, y), c_lines[0], font=f_c, fill=TEXT)
            y += 66

    centered(img, top + 40, H - 300, q_body, bias=0.3)
    swipe_hint(d, accent, "考えたらスワイプ →")
    slides.append(img)

    # 2. 正解と全文訳
    img, d = background()
    top = header(d, label, accent, sub)

    def a_body(d):
        y = 0
        if it.get("format") == "quiz" and it.get("answer_index") is not None:
            ans = it["choices"][it["answer_index"]]
            d.text((MARGIN, y), "正解", font=font("sans", "bold", 36), fill=accent)
            y += 66
            f_a, a_lines = fit(f"{'ABCD'[it['answer_index']]}. {ans}", "serif", "bold", inner, 80, 44, 2)
            y = draw_lines(d, (MARGIN, y), a_lines, f_a, TEXT, leading=1.3)
            y += 70
        d.text((MARGIN, y), "全文訳", font=font("sans", "bold", 36), fill=accent)
        y += 76
        f_t, t_lines = fit(it["translation_ja"], "sans", "regular", inner, 50, 32, 8)
        draw_lines(d, (MARGIN, y), t_lines, f_t, TEXT, leading=1.65)

    centered(img, top + 40, H - 200, a_body)
    slides.append(img)

    # 3. 解説
    img, d = background()
    top = header(d, label, accent, sub)

    def e_body(d):
        d.text((MARGIN, 0), "解説", font=font("sans", "bold", 36), fill=accent)
        f_e, e_lines = fit(it["explanation_ja"], "sans", "regular", inner, 46, 28, 13)
        draw_lines(d, (MARGIN, 76), e_lines, f_e, TEXT, leading=1.7)

    centered(img, top + 40, H - 200, e_body)
    slides.append(img)

    slides.append(_closing(
        label, accent, "日をあけて、\nもう一度読もう。",
        f"英文・設問・全文訳つきの問題を全{total}問、\n{DOMAIN} で無料公開中。", handle))
    return slides


# --- 仕上げ -----------------------------------------------------------------

def finish(slides):
    """全スライドにページ番号を入れて返す。"""
    n = len(slides)
    for i, img in enumerate(slides, 1):
        footer(ImageDraw.Draw(img), i, n)
    return slides


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
    title = cur.get("cover_title")
    return finish(word_slides(series, cur["card_rows"], number, meta["total"], handle, title))


def _cli():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    ap = argparse.ArgumentParser()
    ap.add_argument("what", help="uscpa / legal / training:<cat> / reading")
    ap.add_argument("--cursor", type=int, default=0)
    ap.add_argument("--id", type=int, default=1)
    ap.add_argument("--out", default="out/ig")
    args = ap.parse_args()
    import auto_post as ap_mod  # 本番と同じ抽出ロジックを通す
    if args.what == "reading":
        items = sorted((it for _, it in ap_mod.reading.load_items() if it.get("status") != "rejected"),
                       key=lambda x: x["id"])
        idx = next(i for i, it in enumerate(items) if it["id"] == args.id)
        acc = {"content": "reading", "cursor": idx}
    elif args.what.startswith("training:"):
        cat = args.what.split(":", 1)[1]
        rot = ap_mod.ftp.ROTATION.index(cat)
        acc = {"content": "training", "rot_index": rot, "cursors": {cat: args.cursor}}
    else:
        acc = {"content": args.what, "cursor": args.cursor}
    cur = ap_mod.build_current(acc)
    paths = save(slides_for(acc, cur), args.out, args.what.replace(":", "-"))
    for p in paths:
        print(p)


if __name__ == "__main__":
    _cli()
