"""トップ・SNS紹介・教材紹介・404。"""
from lib.render import esc
from templates import blog as blog_tpl
from templates import layout

SNS_ICONS = {"reading": "📖", "uscpa": "📊", "legal": "⚖️", "kotsukotsu": "✍️"}


def _sns_card(key, sns, heading="h3"):
    return f"""
<div class="sns-card sns-{key}">
  <div class="sns-avatar">{SNS_ICONS.get(key, "📱")}</div>
  <div>
    <{heading}>{esc(sns["label"])}</{heading}>
    <span class="handle">{esc(sns["platform"])}・{esc(sns["handle"])}</span>
    <p>{esc(sns["description"])}</p>
    <a class="follow-btn" href="{esc(sns["url"])}" rel="noopener" target="_blank">フォローする</a>
  </div>
</div>"""


def render_home(cfg, *, reading_count, uscpa_count, legal_count, training_count, articles):
    latest = ""
    if articles:
        items = "".join(
            f'<a class="list-item" href="{blog_tpl.article_url(a)}">'
            f'<h3>{esc(a["title"])}</h3>'
            f'<span class="article-date">{esc(a["date"])}</span></a>'
            for a in articles[:3])
        latest = f"""
<div class="section-head"><h2>ブログ</h2><a class="more" href="/blog/">すべて見る →</a></div>
<div class="article-list">{items}</div>"""

    sns_cards = "".join(_sns_card(k, s) for k, s in cfg["sns"].items())

    content = f"""
<section class="hero">
  <h1>{esc(cfg["tagline"])}</h1>
  <p>{esc(cfg["description"])}</p>
</section>

<div class="card-grid">
  <a class="card card-reading" href="/reading/">
    <span class="card-icon">📖</span>
    <h2>英文解釈トレーニング</h2>
    <p>一文をどこまで正確に読めるか。構文・語法・論理の急所を突くクイズ形式の問題集。</p>
    <div class="card-meta">全{reading_count}問・B2〜C2・解説つき</div>
  </a>
  <a class="card card-uscpa" href="/vocab/uscpa/">
    <span class="card-icon">📊</span>
    <h2>USCPA英単語</h2>
    <p>米国公認会計士試験の頻出英単語を科目別に。FAR・AUD・REG・BAR・ISC・TCP。</p>
    <div class="card-meta">全{uscpa_count}語・科目別フラッシュカード</div>
  </a>
  <a class="card card-legal" href="/vocab/legal/">
    <span class="card-icon">⚖️</span>
    <h2>法律英単語</h2>
    <p>契約書・訴訟・会社法など、実務で出会う法律英語を分野別に。</p>
    <div class="card-meta">全{legal_count}語・分野別フラッシュカード</div>
  </a>
  <a class="card card-training" href="/training/">
    <span class="card-icon">✍️</span>
    <h2>英単語トレーニング</h2>
    <p>英検準1級・ニュース・ドラマ・句動詞・イディオム。めくって覚えるフラッシュカード。</p>
    <div class="card-meta">全{training_count}語・フラッシュカード</div>
  </a>
</div>

<div class="section-head"><h2>SNSで毎日配信中</h2><a class="more" href="/sns/">アカウント紹介 →</a></div>
{sns_cards}

{latest}

<div class="section-head"><h2>おすすめ教材</h2><a class="more" href="/books/">教材一覧 →</a></div>
<p class="lead">Kindleで読める英語学習書など、当サイトと相性のよい教材を紹介しています。</p>
"""
    jsonld = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": cfg["site_name"],
        "description": cfg["description"],
        "url": cfg["base_url"] + "/",
        "inLanguage": "ja",
    }
    return layout.page(
        cfg, title=cfg["site_name"], description=cfg["description"],
        path="/", content=content, jsonld=jsonld)


def render_sns(cfg):
    cards = "".join(_sns_card(k, s, heading="h2") for k, s in cfg["sns"].items())
    content = f"""
<h1>SNSアカウント紹介</h1>
<p class="lead">当サイトのコンテンツは、Threadsの3つのアカウントで毎日配信しています。
スキマ時間の学習にはSNS、じっくり復習にはこのサイト、という使い分けがおすすめです。</p>
{cards}
"""
    return layout.page(
        cfg, title="SNSアカウント紹介",
        description="英文解釈・USCPA英単語・法律英単語を毎日配信するThreadsアカウントの紹介。",
        path="/sns/", content=content,
        breadcrumbs=[("/sns/", "SNS")], active_nav="/sns/")


def render_books(cfg):
    content = """
<h1>おすすめ教材</h1>
<p class="lead">当サイトの学習と相性のよい教材を厳選して紹介します。</p>

<h2>Kindleで読める英語学習書</h2>
<div class="note-box">📚 紹介書籍は現在準備中です。公開までしばらくお待ちください。</div>

<h2>英文解釈をさらに深める</h2>
<div class="note-box">📖 精読・構文解析の定番書などを準備中です。</div>

<h2>USCPA・法律英語の学習リソース</h2>
<div class="note-box">🎓 専門分野の英語教材・講座などを準備中です。</div>
"""
    return layout.page(
        cfg, title="おすすめ教材",
        description="英文解釈・USCPA・法律英語の学習に役立つKindle書籍などの教材紹介。",
        path="/books/", content=content,
        breadcrumbs=[("/books/", "教材")], active_nav="/books/")


def render_404(cfg):
    content = """
<section class="hero">
<h1>ページが見つかりません</h1>
<p>お探しのページは移動または削除された可能性があります。</p>
</section>
<div class="card-grid">
  <a class="card" href="/"><h3>トップページへ</h3><p>サイトの入口から探す</p></a>
  <a class="card" href="/reading/"><h3>英文解釈</h3><p>問題一覧を見る</p></a>
  <a class="card" href="/vocab/"><h3>専門英単語</h3><p>単語帳一覧を見る</p></a>
  <a class="card" href="/training/"><h3>英単語トレーニング</h3><p>確認とディクテーション</p></a>
</div>
"""
    return layout.page(
        cfg, title="404 Not Found",
        description="ページが見つかりません。",
        path="/404.html", content=content)
