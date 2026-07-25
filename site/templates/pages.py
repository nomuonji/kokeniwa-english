"""トップ・SNS紹介・教材紹介・404。"""
from lib.render import esc
from templates import blog as blog_tpl
from templates import layout

SNS_ICONS = {"reading": "📖", "uscpa": "📊", "legal": "⚖️", "kotsukotsu": "✍️"}


def _sns_card(key, sns, heading="h3"):
    """SNSアカウントカード。

    アイコンは Threads のプロフィール画像を static/sns/ に取り込んで自己ホストする。
    CDN(scontent.cdninstagram.com)のURLは署名に有効期限があり直リンクだと切れるため。
    アイコンを差し替えたいときは同じパスの画像を置き換える。
    """
    name = sns.get("display_name") or sns["label"]
    icon = sns.get("icon")
    avatar = (f'<img src="{esc(icon)}" alt="{esc(name)}のアイコン" '
              f'width="320" height="320" loading="lazy">'
              if icon else f'<span class="sns-emoji">{SNS_ICONS.get(key, "📱")}</span>')
    cadence = (f'<span class="sns-cadence">{esc(sns["cadence"])}</span>'
               if sns.get("cadence") else "")
    return f"""
<div class="sns-card sns-{key}">
  <div class="sns-avatar">{avatar}</div>
  <div class="sns-body">
    <{heading}>{esc(name)}</{heading}>
    <span class="handle">{esc(sns["handle"])}{cadence}</span>
    <p>{esc(sns["description"])}</p>
    <a class="follow-btn" href="{esc(sns["url"])}" rel="noopener" target="_blank">
      {esc(sns["platform"])}でフォロー</a>
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

<div class="section-head"><h2>Kindle教材</h2><a class="more" href="/books/">くわしく見る →</a></div>
<p class="lead">当サイトの学習コンテンツをもとに作った「英語トレーニングシリーズ」全3巻。
単語の例文や英文解釈の詳しい解説は、Kindle版に収録しています。
<strong>3冊とも Kindle Unlimited の読み放題対象</strong>です。</p>
<div class="book-strip">{_book_strip()}</div>
{_AFFILIATE_NOTICE}
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
<p class="lead">当サイトのコンテンツは、Threadsの4つのアカウントで毎日配信しています。
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


# 自社Kindle書籍。2つのシリーズを扱う。
#   KINDLE_BOOKS       … 英語トレーニングシリーズ（レーベル: Kokeniwa English）
#   BILINGUAL_BOOKS    … 名作で学ぶ英語多読シリーズ（レーベル: 名著翻訳ラボ）
#
# 全冊 KDP セレクト登録済み＝Kindle Unlimited 対象（2026-07-25 時点で確認）。
# セレクトを外した本が出たら ku: False を持たせてバッジを消すこと。
#
# asin が None の本はまだ Amazon の審査中で商品ページが存在しないため、
# 「近日公開」として表示しリンクを張らない（リンク切れを作らないため）。
# 販売開始後に asin を埋めて再デプロイすれば購入ボタンが出る。
KINDLE_BOOKS = [
    {
        "slug": "uscpa",
        "volume": 1,
        "title": "USCPA頻出英単語1000",
        "subtitle": "科目別・例文対訳つき",
        "asin": "B0HBJ6BKVZ",
        "price": "¥500",
        "cover": "/static/covers/uscpa.jpg",
        "icon": "📊",
        "lead": "米国公認会計士（USCPA）試験に頻出する英単語1,000語を、"
                "現行試験の6科目にそって整理した単語帳です。",
        "points": [
            "現行試験（CPA Evolution 以降）の科目区分に準拠",
            "全1,000語に定訳と「1文の例文＋和訳」つき",
            "FAR 330 / AUD 160 / REG 200 / BAR 120 / ISC 90 / TCP 100",
        ],
        "site_link": ("/vocab/uscpa/", "サイトで単語を確認する"),
    },
    {
        "slug": "legal",
        "volume": 2,
        "title": "法律英単語1000",
        "subtitle": "分野別・例文対訳つき",
        "asin": "B0GYRD22QP",
        "price": "¥500",
        "cover": "/static/covers/legal.jpg",
        "icon": "⚖️",
        "lead": "契約・会社法・訴訟・知的財産・労働・金融など、"
                "法律実務の主要10分野から頻出する英単語1,000語を集めました。",
        "points": [
            "契約書・会社法・訴訟など10分野を分野別に整理",
            "全1,000語に定訳と「1文の例文＋和訳」つき",
            "英文契約書を読み始めた方の最初の一冊に",
        ],
        "site_link": ("/vocab/legal/", "サイトで単語を確認する"),
    },
    {
        "slug": "reading",
        "volume": 3,
        "title": "英文解釈トレーニング200問",
        "subtitle": "日英対訳で読み解く英文法・構文",
        "asin": "B0HBJPK81Z",
        "price": "¥500",
        "cover": "/static/covers/reading.jpg",
        "icon": "📖",
        "lead": "主語と述語の発見・節の切れ目・修飾関係・比較・倒置・省略など、"
                "英文解釈でつまずきやすいポイントを200問に凝縮しました。",
        "points": [
            "選択式59問＋和訳141問。手を動かして構造を確認",
            "全問に自然な和訳と、なぜそう読むのかの詳しい解説つき",
            "基礎★→標準★★→実戦★★★の難易度順",
        ],
        "site_link": ("/reading/", "サイトで問題を解く"),
    },
]

# 名作で学ぶ英語多読シリーズ（レーベル: 名著翻訳ラボ）。版権切れの名著を一文ごとの対訳に。
BILINGUAL_BOOKS = [
    {
        "slug": "holmes",
        "title": "シャーロック・ホームズの冒険",
        "subtitle": "日英対訳版",
        "author": "アーサー・コナン・ドイル",
        "asin": "B0G8KQLQ5D",
        "price": "¥300",
        "cover": "/static/covers/holmes.jpg",
        "icon": "🔍",
        "lead": "全12編の短編を、一文ごとの日英対訳で。"
                "推理を追いながら、自然と英文を読み進められます。",
    },
    {
        "slug": "woolf",
        "title": "自分だけの部屋",
        "subtitle": "A Room of One's Own（英日対訳）",
        "author": "ヴァージニア・ウルフ",
        "asin": "B0G7RXQHM9",
        "price": "¥300",
        "cover": "/static/covers/woolf.jpg",
        "icon": "🚪",
        "lead": "「女性が小説を書くには、お金と自分だけの部屋が必要である」。"
                "近代エッセイの名作を一文ごとの対訳で読みます。",
    },
    {
        "slug": "marx",
        "title": "共産党宣言",
        "subtitle": "日英対訳 ─ 英語で読む歴史的名著",
        "author": "カール・マルクス",
        "asin": "B0G9M1VB9V",
        "price": "¥300",
        "cover": "/static/covers/marx.jpg",
        "icon": "📜",
        "lead": "世界を動かした歴史的文書を、英語原文と日本語訳で。"
                "硬質な論説文を読む練習にも向いています。",
    },
]


# Amazonアソシエイト。既存のAmazon URLに tag= を付けるだけで成立する。
# 表示にあたっては景品表示法・アソシエイト規約により、
# 広告である旨の明示（_AFFILIATE_NOTICE）を同じページに必ず出すこと。
ASSOCIATE_TAG = "kokeniwa-22"
KU_LANDING = "https://www.amazon.co.jp/kindle-dbs/hz/subscribe/ku"

_AFFILIATE_NOTICE = (
    '<p class="affiliate-note">※ 当サイトは Amazon.co.jp アソシエイトとして、'
    '適格販売により収入を得ています。</p>')


def with_tag(url):
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}tag={ASSOCIATE_TAG}"


def amazon_url(asin):
    return with_tag(f"https://www.amazon.co.jp/dp/{asin}")


def _book_strip():
    """トップページ用の表紙サムネイル列。クリックで /books/ へ。"""
    items = "".join(
        f'<a class="book-thumb" href="/books/">'
        f'<img src="{esc(b["cover"])}" alt="{esc(b["title"])} の表紙" '
        f'width="500" height="800" loading="lazy">'
        f'<span>{esc(b["title"])}</span></a>'
        for b in KINDLE_BOOKS)
    return items


def _book_card(b):
    points = "".join(f"<li>{esc(p)}</li>" for p in b["points"])
    if b["asin"]:
        buy = (f'<a class="follow-btn" href="{esc(amazon_url(b["asin"]))}" '
               f'rel="noopener" target="_blank">Amazonで見る（{esc(b["price"])}）</a>')
        status = ""
    else:
        buy = '<span class="book-soon">近日公開</span>'
        status = '<p class="book-status">現在Amazonで審査中です。公開までしばらくお待ちください。</p>'
    path, label = b["site_link"]
    return f"""
<article class="book-card">
  <div class="book-cover">
    <img src="{esc(b["cover"])}" alt="{esc(b["title"])} の表紙"
         width="500" height="800" loading="lazy">
    <span class="ku-badge">Kindle Unlimited 対象</span>
  </div>
  <div class="book-body">
    <span class="book-vol">英語トレーニングシリーズ 第{b["volume"]}巻</span>
    <h3>{b["icon"]} {esc(b["title"])}</h3>
    <p class="book-sub">{esc(b["subtitle"])}</p>
    <p>{esc(b["lead"])}</p>
    <ul class="book-points">{points}</ul>
    {status}
    <p class="book-actions">{buy}<a class="book-sitelink" href="{esc(path)}">{esc(label)} →</a></p>
  </div>
</article>"""


def _bilingual_card(b):
    """対訳シリーズ用のコンパクトなカード。"""
    return f"""
<article class="bl-card">
  <div class="book-cover">
    <img src="{esc(b["cover"])}" alt="{esc(b["title"])} の表紙" loading="lazy">
    <span class="ku-badge">Kindle Unlimited 対象</span>
  </div>
  <div class="bl-body">
    <h3>{b["icon"]} {esc(b["title"])}</h3>
    <p class="book-sub">{esc(b["author"])}｜{esc(b["subtitle"])}</p>
    <p>{esc(b["lead"])}</p>
    <p class="book-actions">
      <a class="follow-btn" href="{esc(amazon_url(b["asin"]))}"
         rel="noopener" target="_blank">Amazonで見る（{esc(b["price"])}）</a>
    </p>
  </div>
</article>"""


def render_books(cfg):
    cards = "".join(_book_card(b) for b in KINDLE_BOOKS)
    bl_cards = "".join(_bilingual_card(b) for b in BILINGUAL_BOOKS)
    content = f"""
<h1>Kindle教材</h1>
<p class="lead">英語学習のためのKindle書籍を2シリーズ、全6冊出版しています。
当サイトの学習コンテンツをまとめた<strong>英語トレーニングシリーズ</strong>と、
名著を一文ごとの対訳で読む<strong>名作で学ぶ英語多読シリーズ</strong>です。</p>

<div class="ku-hero">
  <div class="ku-hero-body">
    <span class="ku-hero-label">Kindle Unlimited 対象</span>
    <h2>6冊とも読み放題で読めます</h2>
    <p>Kindle Unlimited に登録すると、両シリーズの全6冊を追加料金なしで読めます。
    初めての方は30日間の無料体験があります。</p>
    <p class="ku-hero-actions">
      <a class="follow-btn" href="{esc(with_tag(KU_LANDING))}"
         rel="noopener" target="_blank">Kindle Unlimited を見る</a>
    </p>
  </div>
</div>

<h2>英語トレーニングシリーズ</h2>
<p>当サイトの問題・単語をもとにした学習書。全3巻。</p>
<div class="book-list">{cards}</div>

<h2>名作で学ぶ英語多読シリーズ</h2>
<p>版権切れの名著を、一文ごとの日英対訳で読むシリーズ。
辞書を引く手を止めずに、名作をそのまま英語で味わえます。全3巻・各¥300。</p>
<div class="bl-list">{bl_cards}</div>

<h2>サイトとの違い</h2>
<p>当サイトでは、英単語は<strong>見出し語と定訳</strong>まで、英文解釈は
<strong>英文・設問・正解・全文訳</strong>まで無料で公開しています。
Kindle版には、これに加えて<strong>単語の例文と対訳</strong>、
<strong>英文解釈の詳しい解説</strong>を収録しています。</p>

<h2>読者特典</h2>
<p>各書籍には、内容をそのまま暗記アプリ <strong>Anki</strong> に取り込める
学習用データの特典がついています。ダウンロード方法は書籍の巻末に記載しています。</p>

{_AFFILIATE_NOTICE}
"""
    return layout.page(
        cfg, title="Kindle教材",
        description="英文解釈・USCPA英単語・法律英単語のKindle教材「英語トレーニングシリーズ」全3巻。"
                    "Kindle Unlimited 対象です。",
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
