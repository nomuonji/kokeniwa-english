"""ブログ（content/blog/*.md → /blog/）。"""
import re

from lib.render import esc
from templates import layout

# front matter の topic → (CSSのアクセントクラス, アイコン)
# 未登録の topic はデフォルト（苔緑）で表示する。
TOPICS = {
    "英文解釈": ("reading", "📖"),
    "英単語": ("training", "✍️"),
    "会計英語": ("uscpa", "📊"),
    "法律英語": ("legal", "⚖️"),
    "学習法": ("study", "🌱"),
}

_TAG_RE = re.compile(r"<[^>]+>")


def article_url(article):
    return f"/blog/{article['slug']}/"


def reading_minutes(article):
    """本文の文字数から読了目安（分）を出す。日本語は約500字/分で計算。"""
    return max(1, round(len(_TAG_RE.sub("", article["html"])) / 500))


def _topic(article):
    name = article.get("topic") or ""
    cls, icon = TOPICS.get(name, ("study", "🌱"))
    return name, cls, icon


def _topic_badge(article):
    name, _, icon = _topic(article)
    if not name:
        return ""
    return f'<span class="post-topic">{icon} {esc(name)}</span>'


def _meta_line(article):
    return (f'<span class="post-meta"><time datetime="{esc(article["date"])}">'
            f'{esc(article["date"])}</time>'
            f'<span class="dot" aria-hidden="true">・</span>'
            f'約{reading_minutes(article)}分</span>')


def post_card(article, *, heading="h3", featured=False):
    """記事カード。ブログ一覧とトップの「最新記事」で共用する。"""
    _, cls, _ = _topic(article)
    kind = "post-featured" if featured else "post-card"
    desc = article.get("description", "")
    label = "続きを読む" if featured else "読む"
    return f"""
<a class="{kind} topic-{cls}" href="{article_url(article)}">
  <div class="post-head">{_topic_badge(article)}{_meta_line(article)}</div>
  <{heading} class="post-title">{esc(article["title"])}</{heading}>
  <p class="post-desc">{esc(desc)}</p>
  <span class="post-more">{label} <span aria-hidden="true">→</span></span>
</a>"""


def render_index(cfg, articles):
    if not articles:
        body = '<p>記事は準備中です。</p>'
    else:
        head, rest = articles[0], articles[1:]
        cards = "".join(post_card(a, heading="h2") for a in rest)
        body = (post_card(head, heading="h2", featured=True)
                + (f'<div class="post-grid">{cards}</div>' if cards else ""))
    content = f"""
<header class="page-head">
  <h1>ブログ</h1>
  <p class="lead">英語学習の方法論、教材の使い方、法律英語・会計英語のコラム。
  当サイトの学習コンテンツを、どう使えば続くのかを書いています。</p>
</header>
{body}
"""
    return layout.page(
        cfg, title="ブログ",
        description="英単語の覚え方、英文解釈のやり方、法律英語・会計英語の入門など、"
                    "英語学習の実践的なコラム。",
        path="/blog/", content=content, og_image="blog",
        breadcrumbs=[("/blog/", "ブログ")], active_nav="/blog/")


def render_article(cfg, article, related=()):
    path = article_url(article)
    name, cls, _ = _topic(article)
    related_html = ""
    if related:
        cards = "".join(post_card(a) for a in related)
        related_html = f"""
<section class="related">
  <div class="section-head"><h2>あわせて読みたい</h2>
  <a class="more" href="/blog/">記事一覧 →</a></div>
  <div class="post-grid">{cards}</div>
</section>"""

    content = f"""
<article class="topic-{cls}">
<header class="article-header">
<div class="post-head">{_topic_badge(article)}{_meta_line(article)}</div>
<h1>{esc(article["title"])}</h1>
</header>
<div class="article-body">
{article["html"]}
</div>
</article>
{related_html}
"""
    jsonld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": article["title"],
        "description": article.get("description", ""),
        "datePublished": article["date"],
        "dateModified": article["date"],
        "inLanguage": "ja",
        "image": cfg["base_url"] + "/static/og/blog.png",
        "mainEntityOfPage": cfg["base_url"] + path,
        "author": {"@type": "Organization", "name": cfg["site_name"],
                   "url": cfg["base_url"] + "/"},
        "publisher": {"@type": "Organization", "name": cfg["site_name"],
                      "url": cfg["base_url"] + "/"},
    }
    if name:
        jsonld["articleSection"] = name
    return layout.page(
        cfg, title=article["title"],
        description=article.get("description", article["title"]),
        path=path, content=content, jsonld=jsonld, og_type="article", og_image="blog",
        breadcrumbs=[("/blog/", "ブログ"), (path, article["title"])],
        active_nav="/blog/")
