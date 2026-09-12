"""長文リーディング教材の一覧・精読ページ。

ブログとは分離し、英語本文を主役にしながら、一文訳・精読ポイント・構造チャンク・学習ガイドを
本文の流れの中だけで完結させる。フローティングUIや精読ON/OFFは置かない。
"""
import json

from lib import config
from lib.render import esc
from templates import layout


def article_url(article):
    return f"/reading/articles/{article['slug']}/"


STYLE = r"""
<style>
.reading-library-hero{margin:1.2rem 0 2rem;padding:clamp(1.2rem,4vw,2rem);background:linear-gradient(145deg,var(--surface),var(--accent-reading-soft));border:1px solid var(--border);border-radius:var(--radius-lg);box-shadow:var(--shadow)}
.reading-library-hero .eyebrow,.reading-article-kicker{margin:0 0 .35rem;color:var(--primary);font-weight:700;letter-spacing:.08em;text-transform:uppercase;font-size:.78rem}
.reading-library-hero p{max-width:760px;margin:.55rem 0 0;color:var(--text-muted)}
.reading-article-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin:1.2rem 0 2.5rem}
.reading-article-card{display:block;padding:20px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);box-shadow:var(--shadow);color:var(--text);transition:transform .18s var(--ease-out),box-shadow .18s var(--ease-out),border-color .18s var(--ease-out)}
.reading-article-card:hover{text-decoration:none;transform:translateY(-2px);box-shadow:var(--shadow-lift);border-color:var(--border-strong)}
.reading-article-card h2{margin:.35rem 0 .45rem;font-size:1.2rem}.reading-article-card p{margin:.4rem 0;color:var(--text-muted)}
.reading-card-meta,.reading-article-meta{display:flex;gap:8px;align-items:center;flex-wrap:wrap;color:var(--text-muted);font-size:.86rem}
.reading-pill{display:inline-flex;align-items:center;padding:.18rem .55rem;border-radius:999px;background:var(--accent-reading-soft);color:var(--primary-strong);font-size:.78rem;font-weight:700}
.reading-article-head{margin:1rem 0 1.5rem;padding-bottom:1.25rem;border-bottom:1px solid var(--border)}
.reading-article-head h1{margin:.25rem 0 .55rem}.reading-dek{font-family:var(--font-serif);font-size:1.06rem;color:var(--text-muted);max-width:760px}
.reading-orientation{margin:1rem 0 1rem;padding:14px 16px;background:var(--surface);border:1px solid var(--border);border-left:4px solid var(--primary);border-radius:var(--radius)}
.reading-orientation strong{display:block;margin-bottom:.25rem;color:var(--primary-strong)}
.reading-structure-hint{margin:.7rem 0 1rem;color:var(--text-muted);font-size:.8rem}
.reading-toolbar{margin:1rem 0 1.5rem;padding:10px 0;border-top:1px solid var(--border);border-bottom:1px solid var(--border)}
.reading-toolbar-note{font-size:.85rem;color:var(--text-muted)}
.reading-study-block{position:relative;margin:0 0 1.6rem;padding:clamp(16px,3vw,24px);background:color-mix(in srgb,var(--surface) 92%,transparent);border:1px solid var(--border);border-radius:var(--radius-lg)}
.reading-block-no{position:absolute;top:12px;right:14px;color:var(--border-strong);font-family:var(--font-serif);font-size:.78rem;letter-spacing:.08em}
.reading-sentence-row{margin:0 0 .9rem}
.reading-sentence-line{appearance:none;display:block;width:100%;border:0;background:transparent;color:var(--text);text-align:left;padding:.08rem .1rem;margin:0;border-radius:7px;font-family:Georgia,"Times New Roman",serif;font-size:clamp(1.08rem,2.4vw,1.22rem);line-height:2;cursor:pointer;-webkit-tap-highlight-color:transparent;transition:background .14s var(--ease-out)}
.reading-sentence-line:hover{background:color-mix(in srgb,var(--surface-2) 34%,transparent)}
.reading-sentence-line[aria-expanded="true"]{background:color-mix(in srgb,var(--surface-2) 22%,transparent)}
.reading-sentence-line:focus-visible{outline:2px solid var(--primary);outline-offset:3px}
.reading-plain-sentence{line-height:2}
.reading-chunk{display:inline;background:transparent;padding:0;margin:0;line-height:inherit;font-weight:500}
.reading-chunk.role-subject{color:var(--accent-reading)}
.reading-chunk.role-predicate{color:var(--accent-training)}
.reading-chunk.role-object,.reading-chunk.role-complement{color:var(--accent-uscpa)}
.reading-chunk.role-clause,.reading-chunk.role-relative,.reading-chunk.role-infinitive,.reading-chunk.role-participle{color:var(--accent-legal)}
.reading-chunk.role-modifier{color:var(--text-muted)}
.reading-chunk.role-connector{color:var(--danger);font-weight:700}
.reading-translation{margin:.2rem 0 .8rem;padding:.58rem .75rem;background:var(--surface-2);border-left:3px solid var(--primary);border-radius:0 8px 8px 0;color:var(--text-muted);font-size:.93rem}.reading-translation[hidden]{display:none}
.reading-notes{margin:1rem 0 0;padding-top:.9rem;border-top:1px dashed var(--border)}.reading-notes-label{display:block;margin-bottom:.55rem;color:var(--text-muted);font-size:.78rem;font-weight:700;letter-spacing:.06em}
.reading-note{display:grid;grid-template-columns:auto 1fr;gap:10px;align-items:start;margin:.45rem 0;padding:.55rem .65rem;border-radius:10px;background:var(--surface)}
.reading-note-type{min-width:3.2rem;text-align:center;padding:.12rem .42rem;border-radius:999px;background:var(--accent-reading-soft);color:var(--primary-strong);font-size:.72rem;font-weight:700}.reading-note.type-grammar .reading-note-type{background:var(--accent-training-soft);color:var(--accent-training)}.reading-note.type-nuance .reading-note-type{background:var(--accent-legal-soft);color:var(--accent-legal)}
.reading-note strong{font-family:Georgia,"Times New Roman",serif}.reading-note p{margin:.12rem 0 0;color:var(--text-muted);font-size:.9rem}
.reading-guide{margin:2.5rem 0 1.5rem;padding:clamp(18px,4vw,28px);background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);box-shadow:var(--shadow)}
.reading-guide>h2{margin-top:0}.reading-guide-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.reading-guide-card{padding:14px 16px;background:var(--bg);border:1px solid var(--border);border-radius:var(--radius)}.reading-guide-card h3{margin:.1rem 0 .55rem}.reading-guide-card ul{margin:.35rem 0;padding-left:1.2rem}.reading-guide-card li{margin:.3rem 0}.reading-guide-card.full{grid-column:1/-1}
.reading-question{padding:.7rem 0;border-bottom:1px dashed var(--border)}.reading-question:last-child{border-bottom:0}.reading-question strong{display:block}.reading-answer{margin:.35rem 0 0;color:var(--text-muted)}
.reading-next{margin:2rem 0;padding:16px;border-top:1px solid var(--border);display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
@media(max-width:720px){.reading-article-grid,.reading-guide-grid{grid-template-columns:1fr}.reading-guide-card.full{grid-column:auto}.reading-study-block{padding:16px 14px}.reading-sentence-line{font-size:1.06rem;line-height:1.95;padding:.06rem 0}.reading-note{grid-template-columns:1fr}.reading-note-type{justify-self:start}}
</style>
"""


SCRIPT = r"""
<script>
(function(){
  const sentences=[...document.querySelectorAll('[data-reading-sentence]')];
  const toggleTranslation=(sentence,show)=>{
    const target=document.getElementById(sentence.getAttribute('aria-controls'));
    if(!target)return;
    const next=show===undefined?sentence.getAttribute('aria-expanded')!=='true':show;
    sentence.setAttribute('aria-expanded',next?'true':'false');
    target.hidden=!next;
  };
  sentences.forEach(sentence=>sentence.addEventListener('click',()=>toggleTranslation(sentence)));
})();
</script>
"""


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
  <p>面白い英語を読みながら、一文ごとの日本語訳、文の構造、語彙・表現・ニュアンスまでその場で確認できます。英文は普通の文章として読みやすさを保ちつつ、意味・文法上の塊を文字色で区別しています。</p>
</section>
<p class="lead">まず英文をそのまま読み、色のまとまりで文の構造をつかみます。和訳を確認したい文は、その文自体をタップしてください。</p>
<div class="reading-article-grid">{''.join(cards)}</div>
<section class="note-box">
  <h2>この教材の使い方</h2>
  <p>色名を覚える必要はありません。「どこまでが一つの意味の塊か」を目で追いながら、英文を前からまとまりで処理する感覚を育てます。</p>
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
    return '<aside class="reading-notes"><span class="reading-notes-label">ここで覚える</span>' + "".join(rows) + "</aside>"


def _render_sentence(sentence, p_index, s_index, chunks):
    translation_id = f"translation-{p_index}-{s_index}"
    if chunks:
        spans = []
        for chunk in chunks:
            spans.append(
                f'<span class="reading-chunk role-{esc(chunk["role"])}">{esc(chunk["text"])}</span>'
            )
        sentence_html = " ".join(spans)
    else:
        sentence_html = f'<span class="reading-plain-sentence" lang="en">{esc(sentence["en"])}</span>'
    return f"""
<div class="reading-sentence-row">
  <button type="button" class="reading-sentence-line" lang="en" data-reading-sentence aria-expanded="false" aria-controls="{translation_id}" title="タップして日本語訳を表示">{sentence_html}</button>
  <div class="reading-translation" id="{translation_id}" lang="ja" hidden>{esc(sentence['ja'])}</div>
</div>"""


def _render_block(block, p_index, structure):
    rows = []
    for s_index, sentence in enumerate(block.get("sentences", [])):
        rows.append(_render_sentence(sentence, p_index, s_index, structure.get(sentence["en"], [])))
    return f"""
<section class="reading-study-block">
  <span class="reading-block-no">{p_index + 1:02d}</span>
  <div class="reading-block-text">{''.join(rows)}</div>
  {_render_notes(block.get('notes', []))}
</section>"""


def _guide_list(title, items, full=False):
    if not items:
        return ""
    lis = "".join(f"<li>{esc(item)}</li>" for item in items)
    cls = "reading-guide-card full" if full else "reading-guide-card"
    return f'<section class="{cls}"><h3>{esc(title)}</h3><ul>{lis}</ul></section>'


def _guide(article):
    guide = article.get("guide", {})
    questions = []
    for item in guide.get("comprehension", []):
        questions.append(
            f'<div class="reading-question"><strong>{esc(item.get("q",""))}</strong>'
            f'<p class="reading-answer">{esc(item.get("a",""))}</p></div>'
        )
    return f"""
<section class="reading-guide">
  <h2>学習ガイド</h2>
  <p>{esc(guide.get('summary_ja',''))}</p>
  <div class="reading-guide-grid">
    {_guide_list('重要語彙', guide.get('vocabulary', []))}
    {_guide_list('使える表現', guide.get('phrases', []))}
    {_guide_list('文法・構文', guide.get('grammar', []))}
    {_guide_list('ニュアンス', guide.get('nuance', []))}
    {_guide_list('やさしい言い換え', guide.get('paraphrases', []))}
    {_guide_list('背景・補足', guide.get('background', []))}
    {('<section class="reading-guide-card full"><h3>理解チェック</h3>' + ''.join(questions) + '</section>') if questions else ''}
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
  {('<p class="reading-structure-hint" lang="ja">文字色のまとまりが、意味・文法上の塊です。背景色ではなく文字色で区別するので、複数行に折り返しても自然に追えます。</p>' if structure else '')}
  <div class="reading-toolbar"><span class="reading-toolbar-note">英文をタップすると、その一文の日本語訳を直下に表示・非表示できます。</span></div>
  {blocks}
  {_guide(article)}
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
