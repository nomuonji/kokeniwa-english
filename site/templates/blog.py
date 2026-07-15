"""ブログ（content/blog/*.md → /blog/）。"""
from lib.render import esc
from templates import layout


def article_url(article):
    return f"/blog/{article['slug']}/"


def render_index(cfg, articles):
    items = []
    for a in articles:
        items.append(
            f'<a class="list-item" href="{article_url(a)}">'
            f'<h2>{esc(a["title"])}</h2>'
            f'<p class="en">{esc(a.get("description", ""))}</p>'
            f'<span class="article-date">{esc(a["date"])}</span></a>')
    content = f"""
<h1>ブログ</h1>
<p class="lead">英語学習の方法論、教材の使い方、USCPA・法律英語のコラムなど。</p>
<div class="article-list">{"".join(items) or '<p>記事は準備中です。</p>'}</div>
"""
    return layout.page(
        cfg, title="ブログ",
        description="英語学習の方法論、教材レビュー、USCPA・法律英語のコラム。",
        path="/blog/", content=content,
        breadcrumbs=[("/blog/", "ブログ")], active_nav="/blog/")


def render_article(cfg, article):
    path = article_url(article)
    content = f"""
<article>
<header class="article-header">
<h1>{esc(article["title"])}</h1>
<p class="article-date">{esc(article["date"])}</p>
</header>
<div class="article-body">
{article["html"]}
</div>
</article>
<nav class="pager"><a href="/blog/"><span class="dir">←</span>ブログ一覧へ戻る</a></nav>
"""
    jsonld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": article["title"],
        "description": article.get("description", ""),
        "datePublished": article["date"],
        "inLanguage": "ja",
        "mainEntityOfPage": cfg["base_url"] + path,
        "publisher": {"@type": "Organization", "name": cfg["site_name"]},
    }
    return layout.page(
        cfg, title=article["title"],
        description=article.get("description", article["title"]),
        path=path, content=content, jsonld=jsonld, og_type="article",
        breadcrumbs=[("/blog/", "ブログ"), (path, article["title"])],
        active_nav="/blog/")
