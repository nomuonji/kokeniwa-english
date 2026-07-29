"""ブログ（content/blog/*.md → /blog/）。一覧・トピック別アーカイブ・記事ページ。

記事が増えても壊れない構造にしてある:
  - トピックは front matter の `topic` 一本で決まり、TOPICS に足せば
    アーカイブページ（/blog/topic/{slug}/）も導線も自動で増える
  - カードのサムネと記事のOGP画像は scripts/build_og_images.py が
    記事ごとに生成する。記事を足したら再実行してコミットする
"""
import re
from pathlib import Path

from lib.render import esc
from templates import layout

# front matter の topic → (CSSのアクセントクラス, アイコン, URLスラッグ, アーカイブの説明)
# 未登録の topic はデフォルト（苔緑・アーカイブ無し）で表示する。
TOPICS = {
    "英文解釈": ("reading", "📖", "reading",
              "英文を文法的に「解く」ための記事。構文の見抜き方、訳し方、精読と多読の関係。"),
    "英単語": ("training", "✍️", "vocabulary",
             "単語を覚える方法そのものについての記事。忘却前提の反復、句動詞、英検準1級。"),
    "会計英語": ("uscpa", "📊", "accounting",
             "USCPA・簿記・財務諸表の英語。専門分野は覚える範囲が狭いという話。"),
    "法律英語": ("legal", "⚖️", "legal",
             "英文契約書と法律英語の読み方。条項の型と、頻出する言い回し。"),
    "学習法": ("study", "🌱", "study",
            "続け方の話。教材の選び方、SNSとの組み合わせ、このサイトの使い方。"),
}

_TAG_RE = re.compile(r"<[^>]+>")
_COVER_DIR = Path(__file__).resolve().parent.parent / "static" / "og" / "blog"


def article_url(article):
    return f"/blog/{article['slug']}/"


def topic_url(name):
    return f"/blog/topic/{TOPICS[name][2]}/"


def cover_og(article):
    """記事のOGP画像スラッグ。未生成なら共通のブログ画像に落とす。

    scripts/build_og_images.py を回し忘れても、リンクは切れずに
    共通画像で出る（SNSに壊れたカードを出さないため）。
    """
    slug = article["slug"]
    return f"blog/{slug}" if (_COVER_DIR / f"{slug}.png").is_file() else "blog"


def cover_card(article):
    """一覧カードのサムネ（WebP）。未生成なら None。"""
    slug = article["slug"]
    p = _COVER_DIR / f"{slug}-card.webp"
    return f"/static/og/blog/{slug}-card.webp" if p.is_file() else None


def reading_minutes(article):
    """本文の文字数から読了目安（分）を出す。日本語は約500字/分で計算。"""
    return max(1, round(len(_TAG_RE.sub("", article["html"])) / 500))


def _topic(article):
    name = article.get("topic") or ""
    cls, icon = TOPICS.get(name, ("study", "🌱", "", ""))[:2]
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


def _cover_img(article, *, eager=False):
    """カードのサムネ。alt は空にする。

    見出しがすぐ隣にあり、画像はタイトルを組んだだけの装飾なので、
    読み上げると同じ文言を二度聞かせることになる。
    """
    src = cover_card(article)
    if not src:
        return ""
    loading = "eager" if eager else "lazy"
    return (f'<div class="post-media"><img src="{esc(layout.asset(src))}" alt="" '
            f'width="640" height="336" loading="{loading}" decoding="async"></div>')


def post_card(article, *, heading="h3", featured=False):
    """記事カード。ブログ一覧・トピック別・トップの「最新記事」で共用する。"""
    _, cls, _ = _topic(article)
    kind = "post-featured" if featured else "post-card"
    desc = article.get("description", "")
    label = "続きを読む" if featured else "読む"
    return f"""
<a class="{kind} topic-{cls}" href="{article_url(article)}">
  {_cover_img(article, eager=featured)}
  <div class="post-body">
    <div class="post-head">{_topic_badge(article)}{_meta_line(article)}</div>
    <{heading} class="post-title">{esc(article["title"])}</{heading}>
    <p class="post-desc">{esc(desc)}</p>
    <span class="post-more">{label} <span aria-hidden="true">→</span></span>
  </div>
</a>"""


def _topic_rail(articles, active=None):
    """トピックの横並び導線。件数を出して、記事が薄い分野を隠さない。

    active=None は一覧ページ（「すべて」が現在地）。
    記事が0本のトピックは出さない。空のアーカイブへ送っても意味がないため。
    """
    counts = {}
    for a in articles:
        counts[a.get("topic") or ""] = counts.get(a.get("topic") or "", 0) + 1
    chips = [f'<a class="chip{"" if active else " is-active"}" href="/blog/">'
             f'すべて<span class="chip-count">{len(articles)}</span></a>']
    for name, (cls, icon, slug, _desc) in TOPICS.items():
        n = counts.get(name, 0)
        if not n:
            continue
        cur = " is-active" if name == active else ""
        chips.append(
            f'<a class="chip topic-{cls}{cur}" href="{topic_url(name)}">'
            f'{icon} {esc(name)}<span class="chip-count">{n}</span></a>')
    return f'<nav class="topic-rail" aria-label="トピック">{"".join(chips)}</nav>'


def render_index(cfg, articles):
    if not articles:
        body = '<p>記事は準備中です。</p>'
    else:
        head, rest = articles[0], articles[1:]
        # 先頭1本を大きく置き、残りをグリッドに流す。記事が増えたとき、
        # ここに「もっと読む」やページングを足せば構造は変えずに伸ばせる。
        body = _topic_rail(articles) + post_card(head, heading="h2", featured=True)
        if rest:
            cards = "".join(post_card(a, heading="h2") for a in rest)
            body += ('<div class="section-head"><h2>記事一覧</h2>'
                     f'<span class="section-count">{len(articles)}本</span></div>'
                     f'<div class="post-grid">{cards}</div>')
    content = f"""
<header class="blog-hero">
  <p class="eyebrow">Journal</p>
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
        path="/blog/", content=content, og_image="blog", wide=True,
        breadcrumbs=[("/blog/", "ブログ")], active_nav="/blog/")


def topics_with_articles(articles):
    """記事が1本以上あるトピックだけを [(名前, 記事リスト), ...] で返す。"""
    out = []
    for name in TOPICS:
        arts = [a for a in articles if a.get("topic") == name]
        if arts:
            out.append((name, arts))
    return out


def render_topic(cfg, name, articles, all_articles):
    """トピック別アーカイブ（/blog/topic/{slug}/）。"""
    cls, icon, _slug, desc = TOPICS[name]
    path = topic_url(name)
    head, rest = articles[0], articles[1:]
    body = _topic_rail(all_articles, active=name) + post_card(head, heading="h2", featured=True)
    if rest:
        cards = "".join(post_card(a, heading="h2") for a in rest)
        body += f'<div class="post-grid">{cards}</div>'
    content = f"""
<header class="blog-hero topic-{cls}">
  <p class="eyebrow"><a href="/blog/">ブログ</a></p>
  <h1>{icon} {esc(name)}</h1>
  <p class="lead">{esc(desc)}</p>
  <p class="hero-count">{len(articles)}本の記事</p>
</header>
{body}
"""
    return layout.page(
        cfg, title=f"{name}の記事",
        description=f"{desc}｜{cfg['site_name']}のブログ",
        path=path, content=content, og_image="blog", wide=True,
        breadcrumbs=[("/blog/", "ブログ"), (path, name)], active_nav="/blog/")


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

    # トピックのバッジは、記事からアーカイブへ戻れるリンクにする
    badge = _topic_badge(article)
    if name and badge:
        badge = f'<a class="post-topic-link" href="{topic_url(name)}">{badge}</a>'
    content = f"""
<article class="topic-{cls}">
<header class="article-header">
<div class="post-head">{badge}{_meta_line(article)}</div>
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
        "image": cfg["base_url"] + f"/static/og/{cover_og(article)}.png",
        "mainEntityOfPage": cfg["base_url"] + path,
        "author": {"@type": "Organization", "name": cfg["site_name"],
                   "url": cfg["base_url"] + "/"},
        "publisher": {"@type": "Organization", "name": cfg["site_name"],
                      "url": cfg["base_url"] + "/"},
    }
    if name:
        jsonld["articleSection"] = name
    crumbs = [("/blog/", "ブログ")]
    if name:
        crumbs.append((topic_url(name), name))
    crumbs.append((path, article["title"]))
    return layout.page(
        cfg, title=article["title"],
        description=article.get("description", article["title"]),
        path=path, content=content, jsonld=jsonld, og_type="article",
        og_image=cover_og(article), breadcrumbs=crumbs, active_nav="/blog/")
