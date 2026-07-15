"""英単語トレーニング（旧 english-learner「こつこつ英単語」）。

一般英語の単語帳を「確認」＋「ディクテーション」で学ぶ。
  /training/                … 5カテゴリへの入口（index可）
  /training/{slug}/         … トレーナー本体（noindex、中身はJSが描画）

トレーナーは軽量JSON（static/data/training-{slug}.json）を読み、
  ?ids=1-50,120  … 出題範囲を指定（投稿連動の受け皿。範囲/個別が使える）
を JS(training-trainer.js)が解釈する。データ量が増えてもページ数は一定。

方針:
  - 専門単語（USCPA/法律）と違い、こちらは例文を出す無料コンテンツ
  - トレーナー本体は noindex（?ids= で無限に変種が出るため）、/training/ を検索の受け皿にする
"""
from lib import config
from lib.render import esc
from templates import layout

TRAINER_SCRIPT = '<script src="/static/training-trainer.js" defer></script>'


def set_url(set_key):
    return f"/training/{config.TRAINING_SETS[set_key]['slug']}/"


def build_json(set_key, words):
    """トレーナー用のJSON。例文つき（確認・ディクテーションで使う）。"""
    tset = config.TRAINING_SETS[set_key]
    items = [{
        "id": w["id"], "w": w["word"], "m": w["meaning"],
        "e": w["example"], "ej": w["example_ja"],
    } for w in words]
    return {
        "title": tset["title"], "set": set_key, "slug": tset["slug"],
        "words": items,
    }


def render_training_home(cfg, counts):
    """/training/ — 5カテゴリへの入口（このページはindex可）。"""
    total = sum(counts.values())
    cards = []
    for set_key, tset in config.TRAINING_SETS.items():
        n = counts[set_key]
        cards.append(
            f'<a class="card card-training" href="{set_url(set_key)}">'
            f'<span class="card-icon">{tset["icon"]}</span>'
            f'<h2>{esc(tset["title"])}</h2><p>{esc(tset["description"])}</p>'
            f'<div class="card-meta">全{n}語・確認＋ディクテーション</div></a>')
    content = f"""
<h1>英単語トレーニング</h1>
<p class="lead">英検準1級・ニュース・ドラマ・句動詞・イディオムの一般英単語を、
全{total}語収録。意味を「確認」したあと、実際に書き取る「ディクテーション」で定着させます。
例文つき・すべて無料。</p>
<div class="card-grid">{"".join(cards)}</div>
<div class="note-box">✍️ <strong>使い方：</strong>各カテゴリのページで範囲を選び、
まず「確認」で意味と例文を頭に入れ、「ディクテーション」で単語と例文を実際に入力します。
判定は表記の一致（大文字小文字・記号・スペースは無視）で行います。</div>
"""
    return layout.page(
        cfg, title="英単語トレーニング（英検準1級・ニュース・ドラマ・句動詞・イディオム）",
        description="英検準1級1500語ほか、ニュース・ドラマ・句動詞・イディオムの英単語を確認とディクテーションで学べる無料トレーニング。",
        path="/training/", content=content,
        breadcrumbs=[("/training/", "英単語トレーニング")],
        active_nav="/training/")


def render_trainer(cfg, set_key, words):
    """/training/{slug}/ — トレーナー本体（noindex、中身はJSが描画）。"""
    tset = config.TRAINING_SETS[set_key]
    path = set_url(set_key)
    total = len(words)
    content = f"""
<h1>{esc(tset["title"])}トレーニング</h1>
<p class="lead">全{total}語。範囲を選んで「確認」で覚え、「ディクテーション」で書き取り。
例文つきの完全版のまとめ買いは<a href="/books/">教材ページ</a>から。</p>
<div id="training-app"
     data-src="/static/data/training-{tset["slug"]}.json"
     data-set="{esc(set_key)}"
     data-base="{esc(path)}">
  <p class="lead">読み込み中…</p>
  <noscript>このトレーニングはJavaScriptが必要です。</noscript>
</div>
"""
    return layout.page(
        cfg, title=f"{tset['title']}トレーニング",
        description=f"{tset['description']}",
        path=path, content=content, noindex=True,
        breadcrumbs=[("/training/", "英単語トレーニング"), (path, tset["short"])],
        active_nav="/training/", extra_scripts=TRAINER_SCRIPT)
