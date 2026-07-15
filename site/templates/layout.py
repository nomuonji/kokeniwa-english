"""共通レイアウト（ヘッダ・フッタ・head内メタ）。"""
import json

from lib.render import esc

NAV_ITEMS = [
    ("/reading/", "英文解釈"),
    ("/vocab/uscpa/", "USCPA単語"),
    ("/vocab/legal/", "法律単語"),
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


def page(cfg, *, title, description, path, content, breadcrumbs=None,
         jsonld=None, og_type="website", active_nav=None, extra_scripts="",
         noindex=False):
    """ページ全体のHTMLを返す。

    path: サイトルートからのパス（例 "/reading/1/"）。canonical/OGPに使う。
    breadcrumbs: [(path, label), ...]（トップは自動で先頭に付く）
    jsonld: dict または dictのリスト（BreadcrumbListは自動付与）
    active_nav: NAV_ITEMS のパス（現在地のハイライト用）
    """
    site_name = cfg["site_name"]
    full_title = site_name if path == "/" else f"{title}｜{site_name}"
    canonical = cfg["base_url"] + path

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
<meta name="twitter:card" content="summary">
<link rel="icon" href="/static/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/static/style.css">
{jsonld_html}
</head>
<body>
<a class="skip-link" href="#main">本文へスキップ</a>
<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="/">
      <svg class="brand-mark" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5Z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M4 20.5V5.5M8 8h8M8 11.5h5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      <span>{esc(site_name)}</span>
    </a>
    <nav class="site-nav" aria-label="メイン">{nav_html}</nav>
  </div>
</header>
<main id="main" class="container">
{crumbs_html}
{content}
</main>
<footer class="site-footer">
  <div class="container">
    <p class="footer-brand">{esc(site_name)}</p>
    <p class="footer-tagline">{esc(cfg["tagline"])}</p>
    <nav class="footer-nav" aria-label="フッタ">{nav_html}</nav>
    <p class="copyright">&copy; {esc(site_name)}</p>
  </div>
</footer>
{extra_scripts}
</body>
</html>
"""
