"""英単語トレーニング（旧 english-learner「こつこつ英単語」）。

一般英語の単語帳を、USCPA/法律と同じ**フラッシュカード一覧**で見せる。
  /training/                … 5カテゴリへの入口（index可）
  /training/{slug}/         … カード一覧本体（noindex、中身はJSが描画）

カード本体は軽量JSON（static/data/training-{slug}.json）を読み、
各カードは表(英単語)⇄裏(意味)を個別に反転する。
  #w{id}  … 投稿連動の受け皿（その語のカードへスクロール＆反転＆強調）

方針:
  - 専門語彙（USCPA/法律）とUIを統一（フラッシュカード一覧・確認テスト等は持たない）
  - カード一覧本体は noindex、/training/ を検索の受け皿にする
"""
from lib import config
from lib.render import esc
from templates import layout

TRAINER_SCRIPT = f'<script src="{layout.asset("/static/training-grid.js")}" defer></script>'


def set_url(set_key):
    return f"/training/{config.TRAINING_SETS[set_key]['slug']}/"


def build_json(set_key, words):
    """カード用の軽量JSON。id / 英単語(t) / 意味(m) のみ。"""
    tset = config.TRAINING_SETS[set_key]
    items = [{"id": w["id"], "t": w["word"], "m": w["meaning"]} for w in words]
    return {"title": tset["title"], "set": set_key, "slug": tset["slug"], "words": items}


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
            f'<div class="card-meta">全{n}語・フラッシュカード</div></a>')
    content = f"""
<h1>英単語トレーニング</h1>
<p class="lead">英検準1級・ニュース・ドラマ・句動詞・イディオムの一般英単語を、
全{total}語収録。カードをタップすると英単語⇄意味が裏返ります。すべて無料。</p>
<div class="card-grid">{"".join(cards)}</div>
"""
    return layout.page(
        cfg, title="英単語トレーニング（英検準1級・ニュース・ドラマ・句動詞・イディオム）",
        description="英検準1級1500語ほか、ニュース・ドラマ・句動詞・イディオムの英単語を、めくって覚える無料フラッシュカード。",
        path="/training/", content=content, og_image="training",
        breadcrumbs=[("/training/", "英単語トレーニング")],
        active_nav="/training/")


def render_trainer(cfg, set_key, words):
    """/training/{slug}/ — カード一覧本体（noindex、中身はJSが描画）。"""
    tset = config.TRAINING_SETS[set_key]
    path = set_url(set_key)
    total = len(words)
    content = f"""
<h1>{esc(tset["title"])}フラッシュカード</h1>
<p class="lead">全{total}語から、単語や意味で検索できます。最初は48語ずつ表示。
カードをタップして意味を確かめ、続けたいときは「さらに表示」へ。</p>
<div id="training-app"
     data-src="/static/data/training-{tset["slug"]}.json"
     data-set="{esc(set_key)}"
     data-base="{esc(path)}">
  <p class="lead">読み込み中…</p>
  <noscript>このフラッシュカードはJavaScriptが必要です。</noscript>
</div>
"""
    return layout.page(
        cfg, title=f"{tset['title']}フラッシュカード",
        description=f"{tset['description']}",
        path=path, content=content, noindex=True, og_image="training",
        breadcrumbs=[("/training/", "英単語トレーニング"), (path, tset["short"])],
        active_nav="/training/", extra_scripts=TRAINER_SCRIPT)
