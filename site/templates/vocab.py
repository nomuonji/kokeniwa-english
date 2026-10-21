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

TRAINER_SCRIPT = f'<script src="{layout.asset("/static/vocab-trainer.js")}" defer></script>'


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


def render_vocab_home(cfg, counts, vocab_data):
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
    previews = []
    guides = {
        "uscpa": ("/blog/accounting-english-basics/", "会計英語の基本を読む"),
        "legal": ("/blog/legal-english-contract-terms/", "英文契約書の用語を読む"),
    }
    for key, subject in (("uscpa", "FAR"), ("legal", "CONTRACT")):
        vset = config.VOCAB_SETS[key]
        words = vocab_data[key][subject][:6]
        rows = "".join(
            f'<tr><th scope="row" lang="en">{esc(w["term"])}</th>'
            f'<td>{esc(w["meaning_ja"])}</td>'
            f'<td><a href="{set_url(key)}?subject={subject}#w{w["id"]}">この語を復習</a></td></tr>'
            for w in words)
        href, label = guides[key]
        previews.append(
            f'<section class="vocab-preview"><h2>{esc(vset["title"])}の見本：{subject}</h2>'
            '<div class="vocab-table-wrap" role="region" aria-label="英単語の見本" tabindex="0">'
            f'<table><caption>{esc(vset["title"])}・収録データから6語</caption>'
            '<thead><tr><th scope="col">英単語</th><th scope="col">日本語の意味</th><th scope="col">練習</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div><p><a href="{href}">{label}</a></p></section>')
    content = f"""
<h1>専門英単語フラッシュカード</h1>
<p class="lead">試験・実務に直結する専門英単語を、科目別のフラッシュカードで。
カードをめくって意味を思い出せるかテストできます。すべて無料。</p>
<div class="card-grid">{"".join(cards)}</div>
<div class="note-box">📕 <strong>例文つきの完全版はKindleで。</strong>
当サイトは日々の投稿の復習・自己テスト用です。全語を例文つきでまとめて学びたい方は、
Kindle版（Anki用データのおまけつき）をご検討ください。</div>
<h2>USCPAと法律英語、どちらから始める？</h2>
<p>財務諸表や監査の英文を読むならUSCPA英単語、契約書や訴訟の英文を読むなら法律英単語から始められます。
USCPAはFAR・AUD・REG・BAR・ISC・TCP、法律英語は契約一般・契約条項・会社法などの分野を選べます。
これは当サイトの学習用分類です。試験範囲の網羅や、個々の文書での訳語を保証する一覧ではありません。</p>
{"".join(previews)}
<h2>単語の意味は分かるのに、文が読めないとき</h2>
<p>単語だけを追加する前に、主語・動詞・修飾先を区切ってみてください。
<a href="/blog/inanimate-subject/">無生物主語の訳し方と練習問題</a>では、物や出来事が主語になる文を扱います。
<a href="/reading/">英文解釈の問題一覧</a>では、選択肢と全文訳で読みを確かめられます。</p>
<h2>カードで復習する手順</h2>
<p>科目を一つ選び、意味を思い出してからカードをめくります。間違えた語は検索してもう一度確認。
訳語が複数ある語は、実際に読んでいる文書でどの意味が合うかも確かめてください。
このページは単語と意味の見本、カードは自己テスト用、例文つきのまとまった教材はKindle版という使い分けです。</p>
"""
    return layout.page(
        cfg, title="専門英単語フラッシュカード（USCPA・法律英語）",
        description="USCPA英単語1000語と法律英単語1000語を科目別にめくって覚える無料フラッシュカード。",
        path="/vocab/", content=content, og_image="uscpa",
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
<p class="lead">全{total}語を科目ごとに学べます。表示中の科目から検索し、カードをめくって意味を確認。
最初は48語ずつ表示します。例文は<a href="/books/">Kindle版</a>に収録しています。</p>
<div id="vocab-app"
     data-src="/static/data/{set_key}.json"
     data-set="{set_key}"
     data-base="{esc(path)}">
  <p class="lead">読み込み中…</p>
  <noscript>このフラッシュカードはJavaScriptが必要です。</noscript>
</div>
{sns_html}
"""
    return layout.page(
        cfg, title=f"{vset['title']}フラッシュカード",
        description=f"{vset['description']} 科目別にめくって覚える無料フラッシュカード。",
        path=path, content=content, noindex=True, og_image=set_key,
        breadcrumbs=[("/vocab/", "専門英単語"), (path, vset["title"])],
        active_nav=path, extra_scripts=TRAINER_SCRIPT)
