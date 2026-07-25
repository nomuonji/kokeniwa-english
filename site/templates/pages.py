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


# 読者特典ページ上部に出すお知らせ。
#
# Kindle本は出版後に読者へ更新を届けられないため、告知はこのページ経由になる
# （＝再訪した読者にしか届かないプル型）。暗記アプリのリリース時などは、
# ここを埋めて再デプロイすれば全書籍の特典ページに同時に反映される。
#
# 例:
# KINDLE_ANNOUNCEMENT = {
#     "title": "暗記アプリをリリースしました",
#     "body": "本書のデータをそのまま学習できるアプリを公開しました。",
#     "link": "/app/", "link_label": "アプリを見る",
# }
KINDLE_ANNOUNCEMENT = None


def _kindle_announcement_html():
    a = KINDLE_ANNOUNCEMENT
    if not a:
        return ""
    btn = ""
    if a.get("link"):
        btn = (f'<p><a class="follow-btn" href="{esc(a["link"])}">'
               f'{esc(a.get("link_label", "詳しく見る"))}</a></p>')
    return (f'<div class="note-box"><p>📣 <strong>{esc(a["title"])}</strong><br>'
            f'{esc(a["body"])}</p>{btn}</div>')


# Kindle読者特典ページの定義。書籍ごとに1ページ＝1データにする。
# （1冊買えば全書籍のデータが手に入る状態を避けるため、まとめページは作らない）
KINDLE_BONUS = {
    "reading": {
        "slug": "reading",
        "book": "英文解釈トレーニング200問",
        "icon": "📖",
        "file": "reading_anki.csv",
        "deck": "英文解釈",
        "count": "全200問",
        "desc": "表面に英文と設問、裏面に正解と全文訳が入ります"
                "（詳しい解説は書籍でご確認ください）。"
                "分野・難易度はタグで絞り込めます。",
    },
    "uscpa": {
        "slug": "uscpa",
        "book": "USCPA頻出英単語1000",
        "icon": "📊",
        "file": "uscpa_anki.csv",
        "deck": "USCPA英単語",
        "count": "全1,000語",
        "desc": "表面に見出し語、裏面に定訳が入ります"
                "（例文は書籍でご確認ください）。"
                "FAR/AUD/REG/BAR/ISC/TCP の科目タグで絞り込めます。",
    },
    "legal": {
        "slug": "legal",
        "book": "法律英単語1000",
        "icon": "⚖️",
        "file": "legal_anki.csv",
        "deck": "法律英単語",
        "count": "全1,000語",
        "desc": "表面に見出し語、裏面に定訳が入ります"
                "（例文は書籍でご確認ください）。"
                "契約・会社法・訴訟・知的財産・労働・金融など"
                "10分野のタグで絞り込めます。",
    },
}


def kindle_bonus_url(key):
    return f"/kindle/{KINDLE_BONUS[key]['slug']}/"


def render_kindle_bonus(cfg, key):
    """書籍ごとのKindle読者特典ページ。

    Kindle本からはこのURLだけをリンクし、CSVには直リンクしない。
    - URLが固定なので、配布物が増減しても出版済みの本を差し替えずに済む
    - 書籍ごとにページを分け、他書籍のデータへは導線を作らない
    - noindex＝検索には載せず、書籍の読者だけが辿り着くページ
    """
    b = KINDLE_BONUS[key]
    content = f"""
<h1>{b["icon"]} {esc(b["book"])}　読者特典</h1>
<p class="lead">お読みいただきありがとうございます。
このページでは、本書の内容をそのまま使える学習用データを配布しています。</p>
{_kindle_announcement_html()}

<h2>Anki用データ（無料・登録不要）</h2>
<p>無料の暗記アプリ <strong>Anki</strong> にそのまま取り込めるCSVです。
デッキ名・カード形式はファイル内に指定済みなので、読み込むだけで使えます。</p>

<div class="note-box">
<p><strong>デッキ名：{esc(b["deck"])}</strong>（{esc(b["count"])}）<br>
{esc(b["desc"])}</p>
<p><a class="follow-btn" href="/downloads/{esc(b["file"])}">CSVをダウンロード</a></p>
</div>

<h3>取り込み手順</h3>
<ol>
<li>上のボタンからCSVファイルをダウンロードします。</li>
<li>Ankiを起動し、「ファイル」→「読み込む」を選びます。</li>
<li>ダウンロードしたCSVを選び、そのまま「読み込む」を押せば完了です。</li>
</ol>
<p class="note">※ Anki は第三者が提供するアプリであり、本書とは別のものです。
入手方法や使い方の詳細は公式サイトをご確認ください。</p>

<h2>対応アプリ・配布内容について</h2>
<p>配布データの形式や、対応する学習アプリは今後追加・変更されることがあります。
最新の内容はこのページでご確認ください。URLは変更しませんので、
ブックマークしておくと便利です。</p>

<h2>ブラウザで学習する</h2>
<p>当サイトでも英語学習コンテンツを無料で公開しています。
スマートフォンのブラウザからそのまま学習できます。</p>
<p><a class="follow-btn" href="/">学習サイトを開く</a></p>
"""
    return layout.page(
        cfg, title=f'{b["book"]}　読者特典',
        description=f'{b["book"]}の読者向けに、Anki用の学習データを配布しています。',
        path=kindle_bonus_url(key), content=content,
        breadcrumbs=[(kindle_bonus_url(key), "読者特典")], noindex=True)


def render_kindle_index(cfg):
    """/kindle/ に直接来た人向けの案内。

    ここから各書籍のデータへは意図的にリンクしない
    （書籍の読者だけが、本に記載されたURLから各ページに入る）。
    """
    content = """
<h1>Kindle読者特典</h1>
<p class="lead">書籍ごとに専用のダウンロードページをご用意しています。</p>
<div class="note-box">
<p>お手元の書籍の巻末「読者特典」ページに記載されたURLを、
ブラウザで直接開いてください。</p>
</div>
<h2>ブラウザで学習する</h2>
<p>当サイトでは英語学習コンテンツを無料で公開しています。</p>
<p><a class="follow-btn" href="/">学習サイトを開く</a></p>
"""
    return layout.page(
        cfg, title="Kindle読者特典",
        description="Kindle書籍の読者向け特典ページのご案内。",
        path="/kindle/", content=content,
        breadcrumbs=[("/kindle/", "Kindle読者特典")], noindex=True)


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
