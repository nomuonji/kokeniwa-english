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
.reading-toolbar{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin:1rem 0 1.5rem;padding:10px 0;border-top:1px solid var(--border);border-bottom:1px solid var(--border)}
.reading-toolbar button{appearance:none;border:1px solid var(--border-strong);background:var(--surface);color:var(--text);border-radius:999px;padding:.48rem .8rem;font:inherit;font-size:.86rem;cursor:pointer}.reading-toolbar button:hover{border-color:var(--primary);color:var(--primary-strong)}
.reading-toolbar-note{font-size:.85rem;color:var(--text-muted)}
.reading-study-block{position:relative;margin:0 0 1.6rem;padding:clamp(16px,3vw,24px);background:color-mix(in srgb,var(--surface) 92%,transparent);border:1px solid var(--border);border-radius:var(--radius-lg)}
.reading-block-no{position:absolute;top:12px;right:14px;color:var(--border-strong);font-family:var(--font-serif);font-size:.78rem;letter-spacing:.08em}
.reading-sentence-row{margin:0 0 .9rem}
.reading-sentence-line{display:block;padding:.03rem 0;font-family:Georgia,"Times New Roman",serif;font-size:clamp(1.08rem,2.4vw,1.22rem);line-height:2}
.reading-plain-sentence{line-height:2}
.reading-chunk{appearance:none;display:inline;border:0;border-bottom:1px solid var(--border-strong);background:transparent;color:var(--text);padding:0 .02em .04em;margin:0;border-radius:2px;font:inherit;font-family:inherit;line-height:inherit;cursor:pointer;transition:background .14s var(--ease-out),border-color .14s var(--ease-out)}
.reading-chunk:hover{background:color-mix(in srgb,var(--surface-2) 60%,transparent)}
.reading-chunk[aria-pressed="true"]{background:var(--accent-reading-soft);border-bottom-width:2px}
.reading-chunk:focus-visible{outline:2px solid var(--primary);outline-offset:2px}
.reading-chunk.role-subject{border-color:var(--accent-reading)}
.reading-chunk.role-predicate{border-color:var(--accent-training)}
.reading-chunk.role-object,.reading-chunk.role-complement{border-color:var(--border-strong)}
.reading-chunk.role-clause,.reading-chunk.role-relative,.reading-chunk.role-infinitive,.reading-chunk.role-participle{border-color:var(--accent-legal)}
.reading-chunk.role-modifier{border-bottom-style:dotted;border-color:var(--text-muted)}
.reading-chunk.role-connector{border-bottom-style:double;border-color:var(--primary);font-weight:600;color:inherit}
.reading-translation-toggle{appearance:none;display:inline-block;vertical-align:middle;margin-left:.35rem;border:1px solid var(--border);background:transparent;color:var(--text-muted);border-radius:999px;padding:.08rem .42rem;font:600 .7rem/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;cursor:pointer}.reading-translation-toggle:hover,.reading-translation-toggle[aria-expanded="true"]{border-color:var(--primary);color:var(--primary-strong);background:var(--accent-reading-soft)}
.reading-structure-detail{margin:.2rem 0 .5rem;padding:.48rem 0 .48rem .72rem;background:transparent;border:0;border-left:2px solid var(--border-strong);font-size:.86rem}.reading-structure-detail[hidden]{display:none}.reading-structure-detail-head{display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}.reading-structure-detail-label{display:inline-flex;padding:.06rem .34rem;border-radius:999px;background:var(--surface-2);color:var(--text-muted);font-size:.7rem;font-weight:700}.reading-structure-detail strong{font-family:Georgia,"Times New Roman",serif}.reading-structure-detail p{margin:.16rem 0 0;color:var(--text-muted)}
.reading-translation{margin:.2rem 0 .8rem;padding:.58rem .75rem;background:var(--surface-2);border-left:3px solid var(--primary);border-radius:0 8px 8px 0;color:var(--text-muted);font-size:.93rem}.reading-translation[hidden]{display:none}
.reading-notes{margin:1rem 0 0;padding-top:.9rem;border-top:1px dashed var(--border)}.reading-notes-label{display:block;margin-bottom:.55rem;color:var(--text-muted);font-size:.78rem;font-weight:700;letter-spacing:.06em}
.reading-note{display:grid;grid-template-columns:auto 1fr;gap:10px;align-items:start;margin:.45rem 0;padding:.55rem .65rem;border-radius:10px;background:var(--surface)}
.reading-note-type{min-width:3.2rem;text-align:center;padding:.12rem .42rem;border-radius:999px;background:var(--accent-reading-soft);color:var(--primary-strong);font-size:.72rem;font-weight:700}.reading-note.type-grammar .reading-note-type{background:var(--accent-training-soft);color:var(--accent-training)}.reading-note.type-nuance .reading-note-type{background:var(--accent-legal-soft);color:var(--accent-legal)}
.reading-note strong{font-family:Georgia,"Times New Roman",serif}.reading-note p{margin:.12rem 0 0;color:var(--text-muted);font-size:.9rem}
.reading-guide{margin:2.5rem 0 1.5rem;padding:clamp(18px,4vw,28px);background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);box-shadow:var(--shadow)}
.reading-guide>h2{margin-top:0}.reading-guide-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.reading-guide-card{padding:14px 16px;background:var(--bg);border:1px solid var(--border);border-radius:var(--radius)}.reading-guide-card h3{margin:.1rem 0 .55rem}.reading-guide-card ul{margin:.35rem 0;padding-left:1.2rem}.reading-guide-card li{margin:.3rem 0}.reading-guide-card.full{grid-column:1/-1}
.reading-question{padding:.7rem 0;border-bottom:1px dashed var(--border)}.reading-question:last-child{border-bottom:0}.reading-question strong{display:block}.reading-answer{margin:.35rem 0 0;color:var(--text-muted)}
.reading-next{margin:2rem 0;padding:16px;border-top:1px solid var(--border);display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
@media(max-width:720px){.reading-article-grid,.reading-guide-grid{grid-template-columns:1fr}.reading-guide-card.full{grid-column:auto}.reading-study-block{padding:16px 14px}.reading-sentence-line{font-size:1.06rem;line-height:1.95}.reading-note{grid-template-columns:1fr}.reading-note-type{justify-self:start}}
</style>
"""


SCRIPT = r"""
<script>
(function(){
  const translationButtons=[...document.querySelectorAll('[data-reading-sentence]')];
  const toggleTranslation=(button,show)=>{
    const target=document.getElementById(button.getAttribute('aria-controls'));
    if(!target)return;
    const next=show===undefined?button.getAttribute('aria-expanded')!=='true':show;
    button.setAttribute('aria-expanded',next?'true':'false');
    target.hidden=!next;
  };
  translationButtons.forEach(button=>button.addEventListener('click',()=>toggleTranslation(button)));

  const chunks=[...document.querySelectorAll('[data-structure-chunk]')];
  const closeRowDetails=(row)=>{
    row.querySelectorAll('[data-structure-chunk]').forEach(item=>item.setAttribute('aria-pressed','false'));
    row.querySelectorAll('[data-structure-detail]').forEach(detail=>detail.hidden=true);
  };
  chunks.forEach(button=>button.addEventListener('click',()=>{
    const row=button.closest('.reading-sentence-row');
    if(!row)return;
    const detail=document.getElementById(button.dataset.detail||'');
    if(!detail)return;
    const wasOpen=button.getAttribute('aria-pressed')==='true';
    closeRowDetails(row);
    if(wasOpen)return;
    button.setAttribute('aria-pressed','true');
    const label=detail.querySelector('[data-structure-label]');
    const quote=detail.querySelector('[data-structure-quote]');
    const note=detail.querySelector('[data-structure-note]');
    if(label)label.textContent=button.dataset.label||'構造';
    if(quote)quote.textContent=button.textContent||'';
    if(note)note.textContent=button.dataset.note||'';
    detail.hidden=false;
  }));

  const all=document.querySelector('[data-reading-toggle-all]');
  if(all)all.addEventListener('click',()=>{
    const shouldShow=translationButtons.some(button=>button.getAttribute('aria-expanded')!=='true');
    translationButtons.forEach(button=>toggleTranslation(button,shouldShow));
    all.textContent=shouldShow?'日本語訳をすべて隠す':'日本語訳をすべて表示';
  });
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
            for key in ("text", "role", "label_ja", "note_ja"):
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
  <p>面白い英語を読みながら、一文ごとの日本語訳、文の構造、語彙・表現・ニュアンスまでその場で確認できます。英文は普通の文章として読みやすさを保ちつつ、意味の塊だけ薄く区切っています。</p>
</section>
<p class="lead">まず普通に英文を読み、構造が気になる箇所だけタップ。必要な文だけ「訳」で日本語を開き、最後に学習ガイドで定着させる構成です。</p>
<div class="reading-article-grid">{''.join(cards)}</div>
<section class="note-box">
  <h2>この教材の使い方</h2>
  <p>下線の色を覚える必要はありません。「どこまでが主語か」「どこが述部か」「どの節が何を説明しているか」という境界だけを意識し、英文を前から塊で処理する感覚を育てます。</p>
</section>
"""
    return layout.page(
        cfg,
        title="英語リーディング・精読教材｜楽しく読める長文",
        description="英語リーディング・長文読解・精読の無料教材。面白い英語記事を、一文ごとの日本語訳、文構造の可視化、語彙・構文・ニュアンス解説つきで読めます。",
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
    detail_id = f"structure-{p_index}-{s_index}"
    if chunks:
        buttons = []
        for chunk in chunks:
            buttons.append(
                f'<button type="button" class="reading-chunk role-{esc(chunk["role"])}" '
                f'data-structure-chunk data-detail="{detail_id}" aria-pressed="false" '
                f'data-label="{esc(chunk["label_ja"])}" data-note="{esc(chunk["note_ja"])}">'
                f'{esc(chunk["text"])}</button>'
            )
        sentence_html = " ".join(buttons)
    else:
        sentence_html = f'<span class="reading-plain-sentence" lang="en">{esc(sentence["en"])}</span>'
    detail = ""
    if chunks:
        detail = f"""
  <div class="reading-structure-detail" id="{detail_id}" data-structure-detail lang="ja" hidden>
    <div class="reading-structure-detail-head"><span class="reading-structure-detail-label" data-structure-label></span><strong lang="en" data-structure-quote></strong></div>
    <p data-structure-note></p>
  </div>"""
    return f"""
<div class="reading-sentence-row">
  <div class="reading-sentence-line" lang="en">{sentence_html}<button type="button" class="reading-translation-toggle" data-reading-sentence aria-expanded="false" aria-controls="{translation_id}" title="日本語訳を表示">訳</button></div>
{detail}
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
  {('<p class="reading-structure-hint" lang="ja">薄い下線が文の構造の区切りです。普通に読み進め、気になる塊だけタップすると役割を確認できます。</p>' if structure else '')}
  <div class="reading-toolbar"><span class="reading-toolbar-note">英文はそのまま読めます。構造が気になる塊をタップ、「訳」で日本語訳を開けます。</span><button type="button" data-reading-toggle-all>日本語訳をすべて表示</button></div>
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
        description=f"{article.get('description','')} 文構造の可視化、一文ごとの日本語訳、語彙・構文・ニュアンス解説つきの英語リーディング教材。",
        path=path,
        content=content,
        jsonld=jsonld,
        og_type="article",
        og_image="reading",
        breadcrumbs=[("/reading/", "英文解釈"), ("/reading/articles/", "長文リーディング"), (path, article.get("title_ja", article["title"]))],
        active_nav="/reading/",
        extra_scripts=SCRIPT,
    )