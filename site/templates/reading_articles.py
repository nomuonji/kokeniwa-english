"""長文リーディング教材の一覧・精読ページ。

ブログとは分離し、英語本文を主役にしながら、一文訳・精読ポイント・構造チャンク・学習ガイドを
本文の流れの中で確認できるようにする。訳・構造・解説は必要なときに開く。
"""
import json

from lib import config
from lib.render import esc
from templates import layout


def article_url(article):
    return f"/reading/articles/{article['slug']}/"


STYLE = (f'<link rel="stylesheet" href="{layout.asset("/static/reading-base.css")}">'
         f'<link rel="stylesheet" href="{layout.asset("/static/reader.css")}">')
SCRIPT = f'<script src="{layout.asset("/static/reader.js")}" defer></script>'


def _meta(article):
    bits = [article.get("topic", "読みもの")]
    if article.get("level"):
        bits.append(article["level"])
    if article.get("minutes"):
        bits.append(f"約{article['minutes']}分")
    return " · ".join(esc(x) for x in bits if x)


def _structure_for(article):
    """記事と分離した構造チャンクを読み、本文とのズレをビルド時に検出する。"""
    path = config.CONTENT_DIR / "reading" / "structure" / f"{article['slug']}.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    mapping = data.get("sentences", {})
    if not isinstance(mapping, dict):
        raise ValueError(f"{path.name}: sentences は object にしてください")
    source_sentences = {
        sentence["en"]
        for paragraph in article.get("paragraphs", [])
        for sentence in paragraph.get("sentences", [])
    }
    unknown = set(mapping) - source_sentences
    if unknown:
        raise ValueError(f"{path.name}: 本文に存在しない英文があります: {next(iter(unknown))}")
    for sentence_en, chunks in mapping.items():
        if not isinstance(chunks, list) or not chunks:
            raise ValueError(f"{path.name}: {sentence_en[:32]}... の chunks が空です")
        for index, chunk in enumerate(chunks):
            for key in ("text", "role"):
                if not chunk.get(key):
                    raise ValueError(f"{path.name}: chunk[{index}] に {key} がありません")
        reconstructed = " ".join(chunk["text"].strip() for chunk in chunks)
        if reconstructed != sentence_en:
            raise ValueError(
                f"{path.name}: chunk の連結結果が本文と一致しません\n本文: {sentence_en}\nchunk: {reconstructed}"
            )
    return mapping


def render_index(cfg, articles):
    cards = []
    for article in articles:
        cards.append(f"""
<a class="reading-article-card" href="{article_url(article)}">
  <div class="reading-card-meta"><span class="reading-pill">精読教材</span><span>{_meta(article)}</span></div>
  <h2 lang="en">{esc(article['title'])}</h2>
  <p>{esc(article.get('title_ja',''))}</p>
  <p>{esc(article.get('description',''))}</p>
</a>""")
    content = STYLE + f"""
<section class="reading-library-hero">
  <p class="eyebrow">Kokeniwa Reading Garden</p>
  <h1>英語リーディング・精読教材</h1>
  <p>気になる話題をひとつ選び、英文を一段落ずつ。訳、構文、語彙の解説を手元で確認しながら、自分のペースで読み進められます。</p>
</section>
<p class="lead">まずは本文を読む。迷った一文は「日本語訳を確認」、読み解きたい段落は「語彙・構文を確認」へ。</p>
<div class="reading-article-grid">{''.join(cards)}</div>
<section class="note-box">
  <h2>この教材の使い方</h2>
  <p>訳を見る前に意味を考え、解説で確かめたらもう一度英文へ。記事の最後には、答えを開いて確認できる理解チェックがあります。</p>
</section>
"""
    return layout.page(
        cfg,
        title="英語リーディング・精読教材｜楽しく読める長文",
        description="英語リーディング・長文読解・精読の無料教材。面白い英語記事を、一文タップで開く日本語訳、文構造の色分け、語彙・構文・ニュアンス解説つきで読めます。",
        path="/reading/articles/",
        content=content,
        og_image="reading",
        breadcrumbs=[("/reading/", "英文解釈"), ("/reading/articles/", "長文リーディング")],
        active_nav="/reading/",
        wide=True,
    )


def _render_notes(notes):
    if not notes:
        return ""
    labels = {"word": "重要語", "phrase": "表現", "grammar": "構文", "nuance": "語感"}
    rows = []
    for note in notes:
        kind = note.get("type", "phrase")
        rows.append(
            f'<div class="reading-note type-{esc(kind)}">'
            f'<span class="reading-note-type">{esc(labels.get(kind,"ポイント"))}</span>'
            f'<div><strong lang="en">{esc(note.get("quote",""))}</strong>'
            f'<p>{esc(note.get("explanation_ja",""))}</p></div></div>'
        )
    return '<details class="reading-notes"><summary>語彙・構文を確認 <span class="note-count">' + str(len(notes)) + '</span></summary><div class="reading-notes-body">' + "".join(rows) + '</div></details>'



def _render_sentence(sentence, p_index, s_index, chunks):
    translation_id = f"translation-{p_index}-{s_index}"
    roles = {'subject': '主語', 'predicate': '述語', 'object': '目的語', 'complement': '補語', 'clause': '節', 'relative': '関係節', 'infinitive': '不定詞', 'participle': '分詞', 'modifier': '修飾', 'connector': '接続'}
    if chunks:
        spans = []
        for chunk in chunks:
            role = roles.get(chunk["role"], chunk["role"])
            spans.append(f'<span class="reading-chunk role-{esc(chunk["role"])}" '
                         f'data-role-label="{esc(role)}" title="{esc(role)}">{esc(chunk["text"])}</span>')
        sentence_html = " ".join(spans)
    else:
        sentence_html = f'<span class="reading-plain-sentence">{esc(sentence["en"])}</span>'
    return f"""
<div class="reading-sentence-row" id="sentence-{p_index}-{s_index}">
  <span class="sentence-number" aria-label="文 {p_index + 1}.{s_index + 1}">{p_index + 1}.{s_index + 1}</span>
  <p class="reading-sentence-line" lang="en">{sentence_html}</p>
  <details class="sentence-translation">
    <summary data-reading-sentence aria-controls="{translation_id}">日本語訳を確認</summary>
    <div class="reading-translation" id="{translation_id}" lang="ja">{esc(sentence['ja'])}</div>
  </details>
</div>"""


def _render_block(block, p_index, structure):
    rows = []
    for s_index, sentence in enumerate(block.get("sentences", [])):
        rows.append(_render_sentence(sentence, p_index, s_index, structure.get(sentence["en"], [])))
    return f"""
<section class="reading-study-block" id="paragraph-{p_index + 1}" aria-labelledby="paragraph-title-{p_index + 1}">
  <h2 class="reading-block-no" id="paragraph-title-{p_index + 1}">段落 {p_index + 1:02d}</h2>
  <div class="reading-block-text">{''.join(rows)}</div>
  {_render_notes(block.get('notes', []))}
  <div class="paragraph-actions" data-reader-enhancement hidden><label><input type="checkbox" data-paragraph-complete="{p_index + 1}"> この段落を理解できた</label></div>
</section>"""


def _guide_list(title, items, full=False):
    if not items:
        return ""
    lis = "".join(f"<li>{esc(item)}</li>" for item in items)
    cls = "reading-guide-card full" if full else "reading-guide-card"
    return f'<details class="{cls} guide-topic"><summary>{esc(title)} <span class="note-count">{len(items)}</span></summary><ul>{lis}</ul></details>'


def _guide(article):
    guide = article.get("guide", {})
    questions = []
    for item in guide.get("comprehension", []):
        questions.append(
            f'<div class="reading-question"><strong>{esc(item.get("q",""))}</strong>'
            f'<details class="reading-answer"><summary>答えを確認</summary><p>{esc(item.get("a",""))}</p></details></div>'
        )
    return f"""
<section class="reading-guide" id="study-guide">
  <h2>学習ガイド</h2>
<details class="guide-summary"><summary>全体の要約を確認</summary><p>{esc(guide.get('summary_ja',''))}</p></details>
  <div class="reading-guide-grid">
    {('<section class="reading-guide-card full"><h3>理解チェック</h3>' + ''.join(questions) + '</section>') if questions else ''}
    {_guide_list('重要語彙', guide.get('vocabulary', []))}
    {_guide_list('使える表現', guide.get('phrases', []))}
    {_guide_list('文法・構文', guide.get('grammar', []))}
    {_guide_list('ニュアンス', guide.get('nuance', []))}
    {_guide_list('やさしい言い換え', guide.get('paraphrases', []))}
    {_guide_list('背景・補足', guide.get('background', []))}

    {_guide_list('話す・書く', guide.get('output', []), full=True)}
  </div>
</section>"""


def render_article(cfg, article, prev_article=None, next_article=None):
    path = article_url(article)
    structure = _structure_for(article)
    blocks = "".join(_render_block(block, i, structure) for i, block in enumerate(article.get("paragraphs", [])))
    prev_link = f'<a href="{article_url(prev_article)}">← {esc(prev_article["title_ja"])}</a>' if prev_article else '<span></span>'
    next_link = f'<a href="{article_url(next_article)}">{esc(next_article["title_ja"])} →</a>' if next_article else '<a href="/reading/articles/">教材一覧へ →</a>'
    content = STYLE + f"""
<article class="reading-article-shell">
  <header class="reading-article-head">
    <p class="reading-article-kicker">Reading Garden · Intensive Reading</p>
    <div class="reading-article-meta"><span class="reading-pill">精読教材</span><span>{_meta(article)}</span></div>
    <h1 lang="en">{esc(article['title'])}</h1>
    <p class="reading-dek">{esc(article.get('title_ja',''))} — {esc(article.get('description',''))}</p>
  </header>
  <div class="reading-orientation"><strong>この記事を読むヒント</strong>{esc(article.get('orientation_ja',''))}</div>
  <nav class="reader-steps" aria-label="ページ内メニュー"><a href="#paragraph-1">本文を読む</a><a href="#reader-settings" data-reader-enhancement hidden>読み方を調整</a><a href="#study-guide">理解を確かめる</a></nav>
  <div class="reader-settings" id="reader-settings" data-reader-enhancement hidden>
    <div class="reader-settings-heading"><strong>読みやすさを調整</strong><span>訳と解説は、必要なところだけ開けます。</span></div>
    <div class="reader-options">
      <label class="reader-font-label">文字サイズ <select id="reader-font"><option value="normal">標準</option><option value="large">大きめ</option><option value="larger">さらに大きく</option></select></label>
      {('<label><input type="checkbox" id="reader-structure"> 構文の区切りと役割を表示</label>' if structure else '')}
      <button type="button" id="reader-translations" aria-pressed="false">すべての訳を開く</button>
    </div>
    <p class="structure-help" id="structure-help" hidden>語句の上のラベルは、その語句が文の中で果たす役割です。自然に読めるようになったら表示を外してみましょう。</p>
  </div>
  <div class="reader-progress" data-reader-enhancement hidden><span id="reader-progress-text" role="status"></span><progress id="reader-progress" value="0" max="{len(article.get('paragraphs', []))}" aria-label="確認した段落"></progress><a id="reader-resume" href="#paragraph-1">次の段落へ ↓</a></div>
  {blocks}
  <p class="reader-storage-note" data-reader-enhancement hidden>チェックはこのブラウザに保存されます。いつでも外して復習できます。</p>
  {_guide(article)}
  <p><a href="/reading/articles/">← 精読教材一覧へ</a></p>
  <nav class="reading-next" aria-label="前後の教材">{prev_link}{next_link}</nav>
</article>
"""
    jsonld = [
        {
            "@context": "https://schema.org",
            "@type": "LearningResource",
            "name": article["title"],
            "description": article.get("description", ""),
            "inLanguage": "en",
            "learningResourceType": "Reading exercise",
            "educationalLevel": article.get("level", ""),
            "isAccessibleForFree": True,
        },
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": article["title"],
            "description": article.get("description", ""),
            "inLanguage": "en",
            "datePublished": article.get("date", ""),
        },
    ]
    return layout.page(
        cfg,
        title=f"{article.get('title_ja', article['title'])}｜英語リーディング・精読教材",
        description=f"{article.get('description','')} 文構造の色分け、一文タップで開く日本語訳、語彙・構文・ニュアンス解説つきの英語リーディング教材。",
        path=path,
        content=content,
        jsonld=jsonld,
        og_type="article",
        og_image="reading",
        breadcrumbs=[("/reading/", "英文解釈"), ("/reading/articles/", "長文リーディング"), (path, article.get("title_ja", article["title"]))],
        active_nav="/reading/",
        extra_scripts=SCRIPT,
    )
