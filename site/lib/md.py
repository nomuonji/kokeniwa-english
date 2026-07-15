"""ブログ用の簡易Markdownパーサ（標準ライブラリのみ）。

対応するサブセット:
  front matter（--- で囲む key: value）、見出し(#〜####)、段落、
  箇条書き(- / 1.)、強調(**bold** / *italic*)、コード(`inline` / ```block```)、
  リンク([text](url))、画像(![alt](src))、引用(>)、水平線(---)
これ以外の記法が必要になったら記事側をHTMLで書く（front matterに raw_html: true）。
"""
import html
import re


def parse_front_matter(text):
    """front matterを (meta_dict, 本文) で返す。無ければ ({}, 全文)。"""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    meta = {}
    for line in text[3:end].strip().splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, text[end + 4:].lstrip("\n")


_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC = re.compile(r"\*([^*]+)\*")
_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


def _inline(text):
    """インライン記法をHTMLに変換。先にエスケープし、記法部分だけタグ化する。"""
    text = html.escape(text, quote=False)
    text = _INLINE_CODE.sub(r"<code>\1</code>", text)
    text = _IMAGE.sub(r'<img src="\2" alt="\1" loading="lazy">', text)
    text = _LINK.sub(r'<a href="\2">\1</a>', text)
    text = _BOLD.sub(r"<strong>\1</strong>", text)
    text = _ITALIC.sub(r"<em>\1</em>", text)
    return text


def to_html(body):
    """Markdown本文をHTMLに変換する。"""
    lines = body.splitlines()
    out = []
    paragraph = []
    list_tag = None      # 'ul' | 'ol' | None
    in_code = False
    quote = []

    def flush_paragraph():
        if paragraph:
            out.append(f"<p>{_inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def close_list():
        nonlocal list_tag
        if list_tag:
            out.append(f"</{list_tag}>")
            list_tag = None

    def flush_quote():
        if quote:
            inner = "".join(f"<p>{_inline(q)}</p>" for q in quote)
            out.append(f"<blockquote>{inner}</blockquote>")
            quote.clear()

    for line in lines:
        stripped = line.strip()

        if in_code:
            if stripped.startswith("```"):
                out.append("</code></pre>")
                in_code = False
            else:
                out.append(html.escape(line))
            continue

        if stripped.startswith("```"):
            flush_paragraph(); close_list(); flush_quote()
            lang = html.escape(stripped[3:].strip(), quote=True)
            cls = f' class="language-{lang}"' if lang else ""
            out.append(f"<pre><code{cls}>")
            in_code = True
            continue

        if not stripped:
            flush_paragraph(); close_list(); flush_quote()
            continue

        m = re.match(r"(#{1,4})\s+(.*)", stripped)
        if m:
            flush_paragraph(); close_list(); flush_quote()
            level = max(len(m.group(1)), 2)  # 記事内の見出しは h2 から（h1はタイトル専用）
            out.append(f"<h{level}>{_inline(m.group(2))}</h{level}>")
            continue

        if stripped in ("---", "***"):
            flush_paragraph(); close_list(); flush_quote()
            out.append("<hr>")
            continue

        if stripped.startswith(">"):
            flush_paragraph(); close_list()
            quote.append(stripped.lstrip("> "))
            continue

        m = re.match(r"[-*]\s+(.*)", stripped)
        if m:
            flush_paragraph(); flush_quote()
            if list_tag != "ul":
                close_list()
                out.append("<ul>")
                list_tag = "ul"
            out.append(f"<li>{_inline(m.group(1))}</li>")
            continue

        m = re.match(r"\d+\.\s+(.*)", stripped)
        if m:
            flush_paragraph(); flush_quote()
            if list_tag != "ol":
                close_list()
                out.append("<ol>")
                list_tag = "ol"
            out.append(f"<li>{_inline(m.group(1))}</li>")
            continue

        flush_quote()
        paragraph.append(stripped)

    flush_paragraph(); close_list(); flush_quote()
    if in_code:
        out.append("</code></pre>")
    return "\n".join(out)


def render_article(text):
    """front matter付きMarkdownを (meta, html) で返す。"""
    meta, body = parse_front_matter(text)
    if meta.get("raw_html") == "true":
        return meta, body
    return meta, to_html(body)
