"""共通レイアウト（ヘッダ・フッタ・head内メタ）。"""
import hashlib
import json
from functools import lru_cache
from pathlib import Path

from lib.render import esc

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@lru_cache(maxsize=None)
def asset(path):
    """/static/... に内容ハッシュのクエリを付けて返す。

    _headers で /static/* に Cache-Control: max-age=86400 を設定しているため、
    ファイルを更新しても既存訪問者には最大24時間、古いCSS/JSが使われてしまう。
    （実際にCSS更新後、キャッシュ済みブラウザでレイアウトが崩れた）
    内容が変わったときだけURLが変わるようにして、確実に取り直させる。
    """
    f = _STATIC_DIR / path.removeprefix("/static/")
    if not f.is_file():
        return path
    h = hashlib.sha1(f.read_bytes()).hexdigest()[:8]
    return f"{path}?v={h}"

NAV_ITEMS = [
    ("/reading/", "英文解釈"),
    ("/vocab/uscpa/", "USCPA単語"),
    ("/vocab/legal/", "法律単語"),
    ("/training/", "英単語"),
    ("/blog/", "ブログ"),
    ("/books/", "教材"),
    ("/sns/", "SNS"),
]


def breadcrumb_jsonld(cfg, crumbs):
    items = [{
        "@type": "ListItem",
        "position": i + 1,
        "name": name,
        "item": cfg["base_url"] + path,
    } for i, (path, name) in enumerate(crumbs)]
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}


# 全ページ共通のアナウンスバー。Kindle教材の告知に使う。
#
# text/link を書き換えれば全ページに反映される。告知をやめるときは None にする。
# 閉じるボタンは localStorage に記録し、同じ id のうちは再表示しない。
# 内容を変えたら id も変える（過去に閉じた人にも再度出すため）。
ANNOUNCE = {
    "id": "kindle-2026-07",
    "text": "英語トレーニングシリーズ全3巻を出版しました。対訳シリーズと合わせて全6冊、"
            "Kindle Unlimited の読み放題対象です。",
    "short": "Kindle教材 全6冊を出版しました（Kindle Unlimited 対象）",
    "link": "/books/",
    "link_label": "教材を見る",
}


def _announce_html():
    a = ANNOUNCE
    if not a:
        return ""
    return f"""
<div class="announce" id="announce" data-announce-id="{esc(a["id"])}" hidden>
  <div class="container announce-inner">
    <span class="announce-icon" aria-hidden="true">📚</span>
    <p class="announce-text">
      <span class="announce-full">{esc(a["text"])}</span>
      <span class="announce-short">{esc(a["short"])}</span>
    </p>
    <a class="announce-link" href="{esc(a["link"])}">{esc(a["link_label"])} →</a>
    <button type="button" class="announce-close" aria-label="お知らせを閉じる">×</button>
  </div>
</div>"""


def _sister_html(cfg):
    """フッタの姉妹サイト導線。

    en（日本語話者の英語学習）と ja（英語話者の日本語学習）は読者が
    ほぼ重ならないので、ナビには載せずフッタの1行にとどめる。
    site_config.json の "sister" を消せば非表示になる。
    """
    s = cfg.get("sister")
    if not s:
        return ""
    return (f'<p class="footer-sister">{esc(s["label"])} '
            f'<a href="{esc(s["url"])}" hreflang="{esc(s["lang"])}" rel="noopener">'
            f'{esc(s["name"])}</a>'
            f'<span class="footer-sister-note">{esc(s["note"])}</span></p>')


def page(cfg, *, title, description, path, content, breadcrumbs=None,
         jsonld=None, og_type="website", active_nav=None, extra_scripts="",
         noindex=False, og_image="default"):
    """ページ全体のHTMLを返す。

    path: サイトルートからのパス（例 "/reading/1/"）。canonical/OGPに使う。
    breadcrumbs: [(path, label), ...]（トップは自動で先頭に付く）
    jsonld: dict または dictのリスト（BreadcrumbListは自動付与）
    active_nav: NAV_ITEMS のパス（現在地のハイライト用）
    og_image: /static/og/{名前}.png のスラッグ。scripts/build_og_images.py で生成する
              （default / reading / uscpa / legal / training / books / blog / sns）
    """
    announce_html = _announce_html()
    site_name = cfg["site_name"]
    full_title = site_name if path == "/" else f"{title}｜{site_name}"
    canonical = cfg["base_url"] + path
    # OGP画像は絶対URL必須。内容ハッシュを付けて、差し替え時にSNS側の
    # キャッシュを確実に引き剥がす（Threads/X は URL 単位でキャッシュする）
    og_image_url = cfg["base_url"] + asset(f"/static/og/{og_image}.png")

    jsonld_list = []
    if jsonld:
        jsonld_list.extend(jsonld if isinstance(jsonld, list) else [jsonld])
    crumbs_html = ""
    if breadcrumbs:
        all_crumbs = [("/", "ホーム")] + list(breadcrumbs)
        jsonld_list.append(breadcrumb_jsonld(cfg, all_crumbs))
        parts = []
        for i, (href, label) in enumerate(all_crumbs):
            if i == len(all_crumbs) - 1:
                parts.append(f'<span aria-current="page">{esc(label)}</span>')
            else:
                parts.append(f'<a href="{esc(href)}">{esc(label)}</a>')
        crumbs_html = (
            '<nav class="breadcrumbs" aria-label="パンくず">'
            + '<span class="sep">/</span>'.join(parts) + "</nav>"
        )

    jsonld_html = "".join(
        '<script type="application/ld+json">'
        + json.dumps(j, ensure_ascii=False) + "</script>"
        for j in jsonld_list
    )

    nav_html = "".join(
        f'<a href="{href}"{" class=\"active\"" if href == active_nav else ""}>{label}</a>'
        for href, label in NAV_ITEMS
    )

    return f"""<!DOCTYPE html>
<html lang="{esc(cfg["lang"])}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
{'<meta name="robots" content="noindex,follow">' if noindex else ''}
<meta property="og:type" content="{esc(og_type)}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:site_name" content="{esc(site_name)}">
<meta property="og:locale" content="ja_JP">
<meta property="og:image" content="{esc(og_image_url)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(full_title)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(full_title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{esc(og_image_url)}">
<meta name="theme-color" content="#4d6a38">
<link rel="icon" href="{esc(asset("/static/favicon.svg"))}" type="image/svg+xml">
<link rel="apple-touch-icon" href="{esc(asset("/static/apple-touch-icon.png"))}">
<link rel="alternate" type="application/rss+xml" title="{esc(site_name)} のブログ" href="/feed.xml">
<link rel="stylesheet" href="{esc(asset("/static/style.css"))}">
{jsonld_html}
</head>
<body>
<div class="garden-bg" aria-hidden="true">
  <svg viewBox="0 0 1440 400" preserveAspectRatio="xMidYMax slice" xmlns="http://www.w3.org/2000/svg">
    <path class="g-far" d="M0 214 C 240 150 430 176 620 200 S 1060 150 1440 188 L1440 400 L0 400 Z"/>
    <path class="g-mid" d="M0 300 C 260 250 520 268 760 286 S 1190 302 1440 278 L1440 400 L0 400 Z"/>
    <g class="g-rake" fill="none" stroke-linecap="round">
      <path d="M70 372 A 232 66 0 0 1 534 372"/>
      <path d="M40 382 A 268 80 0 0 1 564 382"/>
      <path d="M8 393 A 300 92 0 0 1 596 393"/>
    </g>
    <g transform="translate(1104 190)">
      <rect class="g-lantern" x="18" y="150" width="54" height="18" rx="3"/>
      <rect class="g-lantern" x="36" y="94" width="18" height="58"/>
      <path class="g-lantern" d="M26 94 L64 94 L57 79 L33 79 Z"/>
      <rect class="g-lantern" x="26" y="47" width="38" height="33" rx="2"/>
      <circle class="g-light" cx="45" cy="63" r="8.5"/>
      <path class="g-lantern" d="M16 47 L74 47 L58 29 L32 29 Z"/>
      <path class="g-lantern" d="M35 29 L55 29 L45 18 Z"/>
      <circle class="g-lantern" cx="45" cy="13" r="5"/>
    </g>
    <path class="g-near" d="M0 360 C 130 322 300 324 470 346 C 620 366 830 350 1010 358 C 1190 366 1330 356 1440 360 L1440 400 L0 400 Z"/>
    <ellipse class="g-stone" cx="300" cy="362" rx="126" ry="48"/>
    <ellipse class="g-stone" cx="140" cy="374" rx="74" ry="31"/>
    <ellipse class="g-stone" cx="486" cy="374" rx="64" ry="27"/>
    <!-- 苔: 石を覆うもこもこの苔キャップ + 苔山 -->
    <g class="g-moss">
      <circle cx="218" cy="352" r="24"/><circle cx="258" cy="345" r="29"/><circle cx="300" cy="341" r="31"/><circle cx="342" cy="345" r="29"/><circle cx="382" cy="352" r="24"/>
      <circle cx="112" cy="367" r="17"/><circle cx="140" cy="362" r="21"/><circle cx="168" cy="367" r="17"/>
      <circle cx="462" cy="368" r="15"/><circle cx="486" cy="363" r="19"/><circle cx="510" cy="368" r="15"/>
      <circle cx="740" cy="352" r="20"/><circle cx="772" cy="346" r="25"/><circle cx="806" cy="351" r="21"/>
      <circle cx="986" cy="356" r="17"/><circle cx="1014" cy="351" r="21"/><circle cx="1044" cy="356" r="17"/>
    </g>
    <g class="g-moss-2">
      <circle cx="270" cy="340" r="14"/><circle cx="312" cy="338" r="15"/><circle cx="352" cy="342" r="12"/>
      <circle cx="132" cy="360" r="9"/><circle cx="480" cy="361" r="8"/>
      <circle cx="760" cy="343" r="11"/><circle cx="792" cy="344" r="10"/><circle cx="1004" cy="349" r="9"/>
    </g>
  </svg>
</div>
<a class="skip-link" href="#main">本文へスキップ</a>
<div class="site-top">
{announce_html}
<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="/">
      <svg class="brand-mark" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5Z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M4 20.5V5.5M8 8h8M8 11.5h5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      <span>{esc(site_name)}</span>
    </a>
    <nav class="site-nav" aria-label="メイン">{nav_html}</nav>
  </div>
</header>
</div>
<main id="main" class="container">
{crumbs_html}
{content}
</main>
<footer class="site-footer">
  <div class="container">
    <p class="footer-brand">{esc(site_name)}</p>
    <p class="footer-tagline">{esc(cfg["tagline"])}</p>
    <nav class="footer-nav" aria-label="フッタ">{nav_html}</nav>
{_sister_html(cfg)}
    <p class="copyright">&copy; {esc(site_name)}</p>
  </div>
</footer>
{extra_scripts}
<script src="{esc(asset("/static/announce.js"))}" defer></script>
</body>
</html>
"""
