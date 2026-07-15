"""語彙（USCPA/法律英単語）— 1枚のフラッシュカード方式。

静的に大量ページを作らず、各単語帳を1ページにまとめ、
  ?subject=far   … 科目チップで切替
  #w{id}         … 投稿連動。その語の科目を開き、その語のカードへスクロール＆反転
を JS(vocab-trainer.js)が解釈して描画する。データ量が増えてもページ数は一定。
科目内の全語をカードで並べ、各カードは表(英単語)⇄裏(意味)を個別に反転する。

方針（収益設計）:
  - カード面は選択不可（casualなコピペ抽出を抑止）
  - 例文はサイトに出さない（Kindle版の価値に残す）→ JSONにexampleを含めない
  - フラッシュカードページは noindex（検索から単語一覧が丸見えになるのを防ぐ）
"""
from lib import config
from lib.render import esc
from templates import layout

TRAINER_SCRIPT = '<script src="/static/vocab-trainer.js" defer></script>'


def set_url(set_key):
    return f"/vocab/{config.VOCAB_SETS[set_key]['slug']}/"


def build_json(set_key, by_subject):
    """フラッシュカード用の軽量JSON。例文は含めない。"""
    vset = config.VOCAB_SETS[set_key]
    subjects = {}
    for subj, meta in vset["subjects"].items():
        if by_subject.get(subj):
            subjects[subj] = {
                "name": meta["name"], "ja": meta["ja"],
                "full": meta["full"], "slug": meta["slug"],
            }
    words = []
    for subj in vset["subjects"]:
        for w in by_subject.get(subj, []):
            words.append({"id": w["id"], "s": subj, "t": w["term"], "m": w["meaning_ja"]})
    words.sort(key=lambda x: x["id"])
    return {"title": vset["title"], "set": set_key, "subjects": subjects, "words": words}


def render_vocab_home(cfg, counts):
    """/vocab/ — 2つの単語帳への入口（このページはindex可）。"""
    cards = []
    for set_key, vset in config.VOCAB_SETS.items():
        total = counts[set_key]
        icon = "📊" if set_key == "uscpa" else "⚖️"
        cards.append(
            f'<a class="card card-{set_key}" href="{set_url(set_key)}">'
            f'<span class="card-icon">{icon}</span>'
            f'<h2>{esc(vset["title"])}</h2><p>{esc(vset["description"])}</p>'
            f'<div class="card-meta">全{total}語・科目別フラッシュカード</div></a>')
    content = f"""
<h1>専門英単語フラッシュカード</h1>
<p class="lead">試験・実務に直結する専門英単語を、科目別のフラッシュカードで。
カードをめくって意味を思い出せるかテストできます。すべて無料。</p>
<div class="card-grid">{"".join(cards)}</div>
<div class="note-box">📕 <strong>例文つきの完全版はKindleで。</strong>
当サイトは日々の投稿の復習・自己テスト用です。全語を例文つきでまとめて学びたい方は、
Kindle版（Anki用データのおまけつき）をご検討ください。</div>
"""
    return layout.page(
        cfg, title="専門英単語フラッシュカード（USCPA・法律英語）",
        description="USCPA英単語1000語と法律英単語1000語を科目別にめくって覚える無料フラッシュカード。",
        path="/vocab/", content=content,
        breadcrumbs=[("/vocab/", "専門英単語")])


def render_trainer(cfg, set_key, by_subject):
    """/vocab/uscpa/ など — 1枚のフラッシュカード（noindex、中身はJSが描画）。"""
    vset = config.VOCAB_SETS[set_key]
    path = set_url(set_key)
    total = sum(len(v) for v in by_subject.values())
    sns = cfg["sns"].get(vset["sns_key"])
    sns_html = ""
    if sns:
        sns_html = (f'<div class="note-box">📲 毎日5語ずつ Threads '
                    f'<a href="{esc(sns["url"])}" rel="noopener" target="_blank">{esc(sns["handle"])}</a> '
                    f'で配信中。流れてきた語をここで復習できます。</div>')

    content = f"""
<h1>{esc(vset["title"])}フラッシュカード</h1>
<p class="lead">全{total}語を一覧表示。各カードをタップすると意味が裏返って出ます。
覚えたい語だけめくってセルフチェックを。例文つきの完全版は<a href="/books/">Kindle版</a>で。</p>
{sns_html}
<div id="vocab-app"
     data-src="/static/data/{set_key}.json"
     data-set="{set_key}"
     data-base="{esc(path)}">
  <p class="lead">読み込み中…</p>
  <noscript>このフラッシュカードはJavaScriptが必要です。</noscript>
</div>
"""
    return layout.page(
        cfg, title=f"{vset['title']}フラッシュカード",
        description=f"{vset['description']} 科目別にめくって覚える無料フラッシュカード。",
        path=path, content=content, noindex=True,
        breadcrumbs=[("/vocab/", "専門英単語"), (path, vset["title"])],
        active_nav=path, extra_scripts=TRAINER_SCRIPT)
