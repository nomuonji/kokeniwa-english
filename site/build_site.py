"""静的サイトビルダー。data/ と content/ から dist/ に全ページを生成する。

使い方:
    python site/build_site.py
確認:
    cd dist && python -m http.server 8000
"""
import datetime as dt
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import config, data_loader, md
from lib.render import esc, write_page
from templates import blog as blog_tpl
from templates import pages as pages_tpl
from templates import reading as reading_tpl
from templates import reading_articles as reading_articles_tpl
from templates import training as training_tpl
from templates import vocab as vocab_tpl


def load_articles():
    articles = []
    blog_dir = config.CONTENT_DIR / "blog"
    if not blog_dir.is_dir():
        return articles
    for path in sorted(blog_dir.glob("*.md")):
        meta, html = md.render_article(path.read_text(encoding="utf-8"))
        if meta.get("draft") == "true":
            continue
        for key in ("title", "date"):
            if key not in meta:
                raise ValueError(f"{path.name}: front matter に {key} がありません")
        articles.append({
            "slug": path.stem,
            "title": meta["title"],
            "date": meta["date"],
            "topic": meta.get("topic", ""),
            "description": meta.get("description", ""),
            "html": html,
        })
    articles.sort(key=lambda a: a["date"], reverse=True)
    return articles


def load_reading_articles():
    """content/reading/*.json の長文精読教材を読み込み、最低限の契約を検査する。"""
    articles = []
    reading_dir = config.CONTENT_DIR / "reading"
    if not reading_dir.is_dir():
        return articles
    for path in sorted(reading_dir.glob("*.json")):
        article = json.loads(path.read_text(encoding="utf-8"))
        for key in ("slug", "title", "title_ja", "date", "description", "paragraphs"):
            if not article.get(key):
                raise ValueError(f"{path.name}: reading article に {key} がありません")
        if article["slug"] != path.stem:
            raise ValueError(f"{path.name}: slug はファイル名と一致させてください")
        if not isinstance(article["paragraphs"], list) or not article["paragraphs"]:
            raise ValueError(f"{path.name}: paragraphs は1件以上必要です")
        for p_index, paragraph in enumerate(article["paragraphs"]):
            sentences = paragraph.get("sentences")
            if not isinstance(sentences, list) or not sentences:
                raise ValueError(f"{path.name}: paragraphs[{p_index}].sentences は1件以上必要です")
            for s_index, sentence in enumerate(sentences):
                if not sentence.get("en") or not sentence.get("ja"):
                    raise ValueError(
                        f"{path.name}: paragraphs[{p_index}].sentences[{s_index}] に en/ja が必要です"
                    )
        articles.append(article)
    articles.sort(key=lambda a: (a["date"], a["slug"]), reverse=True)
    return articles


def build_feed(cfg, articles):
    """ブログのRSS 2.0フィード。全ページの<head>から rel=alternate で参照する。"""
    def rfc822(date):
        # front matter は "2026-07-15" 形式。時刻は 00:00 GMT として扱う
        d = dt.datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc)
        return d.strftime("%a, %d %b %Y %H:%M:%S +0000")

    base = cfg["base_url"]
    items = "\n".join(f"""    <item>
      <title>{esc(a["title"])}</title>
      <link>{base}{blog_tpl.article_url(a)}</link>
      <guid isPermaLink="true">{base}{blog_tpl.article_url(a)}</guid>
      <description>{esc(a.get("description", ""))}</description>
      <pubDate>{rfc822(a["date"])}</pubDate>
    </item>""" for a in articles)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{esc(cfg["site_name"])} のブログ</title>
    <link>{base}/blog/</link>
    <atom:link href="{base}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>{esc(cfg["description"])}</description>
    <language>{esc(cfg["lang"])}</language>
{items}
  </channel>
</rss>
"""


def build(cfg):
    # dist 自体は消さず中身だけ入れ替える（dist を cwd に握るプロセスがいても失敗しない）
    config.DIST_DIR.mkdir(parents=True, exist_ok=True)
    for child in config.DIST_DIR.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    pages = {}       # path("/reading/1/") -> html（リンク検査用に全ページ）
    indexable = set()  # sitemapに載せるパス（noindexは除外）

    def emit(path, html, noindex=False):
        pages[path] = html
        if not noindex:
            indexable.add(path)
        rel = "index.html" if path == "/" else path.lstrip("/")
        if path.endswith("/"):
            rel = path.lstrip("/") + "index.html"
        write_page(rel, html)

    # --- データ読み込み ---
    problems = data_loader.load_reading_problems(cfg)
    uscpa = data_loader.load_vocab("uscpa")
    legal = data_loader.load_vocab("legal")
    vocab_data = {"uscpa": uscpa, "legal": legal}
    training_data = {k: data_loader.load_training(k) for k in config.TRAINING_SETS}
    articles = load_articles()
    reading_articles = load_reading_articles()

    # --- 読解問題 ---
    emit("/reading/", reading_tpl.render_index(cfg, problems))
    for category in {p["category"] for p in problems}:
        emit(reading_tpl.category_url(category),
             reading_tpl.render_category(cfg, problems, category))
    for i, p in enumerate(problems):
        emit(reading_tpl.problem_url(p), reading_tpl.render_problem(cfg, problems, i))

    # --- 長文リーディング教材（ブログとは別系統。精読UIを記事内に統合） ---
    emit("/reading/articles/", reading_articles_tpl.render_index(cfg, reading_articles))
    for i, article in enumerate(reading_articles):
        prev_article = reading_articles[i - 1] if i > 0 else None
        next_article = reading_articles[i + 1] if i + 1 < len(reading_articles) else None
        emit(
            reading_articles_tpl.article_url(article),
            reading_articles_tpl.render_article(cfg, article, prev_article, next_article),
        )

    # --- 語彙（1枚のフラッシュカード＋軽量JSON。カード本体はnoindex） ---
    counts = {k: sum(len(v) for v in vocab_data[k].values()) for k in vocab_data}
    emit("/vocab/", vocab_tpl.render_vocab_home(cfg, counts))
    data_dir = config.DIST_DIR / "static" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    for set_key, by_subject in vocab_data.items():
        emit(vocab_tpl.set_url(set_key),
             vocab_tpl.render_trainer(cfg, set_key, by_subject), noindex=True)
        (data_dir / f"{set_key}.json").write_text(
            json.dumps(vocab_tpl.build_json(set_key, by_subject),
                       ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8")

    # --- 英単語トレーニング（確認＋ディクテーション。本体はnoindex、JSON同梱） ---
    training_counts = {k: len(v) for k, v in training_data.items()}
    emit("/training/", training_tpl.render_training_home(cfg, training_counts))
    for set_key, words in training_data.items():
        emit(training_tpl.set_url(set_key),
             training_tpl.render_trainer(cfg, set_key, words), noindex=True)
        (data_dir / f"training-{config.TRAINING_SETS[set_key]['slug']}.json").write_text(
            json.dumps(training_tpl.build_json(set_key, words),
                       ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8")

    # --- ブログ（記事末尾の関連記事は同トピック優先、足りなければ新しい順で補う） ---
    emit("/blog/", blog_tpl.render_index(cfg, articles))
    for topic_name, topic_articles in blog_tpl.topics_with_articles(articles):
        emit(blog_tpl.topic_url(topic_name),
             blog_tpl.render_topic(cfg, topic_name, topic_articles, articles))
    for a in articles:
        others = [b for b in articles if b["slug"] != a["slug"]]
        same = [b for b in others if b.get("topic") and b["topic"] == a.get("topic")]
        related = (same + [b for b in others if b not in same])[:2]
        emit(blog_tpl.article_url(a), blog_tpl.render_article(cfg, a, related))

    # --- 固定ページ ---
    emit("/", pages_tpl.render_home(
        cfg, reading_count=len(problems), uscpa_count=counts["uscpa"],
        legal_count=counts["legal"], training_count=sum(training_counts.values()),
        articles=articles))
    emit("/sns/", pages_tpl.render_sns(cfg))
    emit("/books/", pages_tpl.render_books(cfg))
    emit("/privacy/", pages_tpl.render_privacy(cfg))
    # Kindle読者特典（本からリンクされる固定URL。検索には載せない）
    # 書籍ごとに1ページ＝1データ。他書籍のデータへは導線を作らない。
    emit("/kindle/", pages_tpl.render_kindle_index(cfg), noindex=True)
    for bonus_key in pages_tpl.KINDLE_BONUS:
        emit(pages_tpl.kindle_bonus_url(bonus_key),
             pages_tpl.render_kindle_bonus(cfg, bonus_key), noindex=True)
    write_page("404.html", pages_tpl.render_404(cfg))

    # --- 静的アセット（static/data は上で作成済みのため dirs_exist_ok） ---
    static_src = config.SITE_DIR / "static"
    shutil.copytree(static_src, config.DIST_DIR / "static", dirs_exist_ok=True)

    # --- CSVダウンロード（Ankiインポート用。Kindleおまけ。表からはリンクしない） ---
    anki_dir = config.ROOT / "anki"
    if anki_dir.is_dir():
        dl_dir = config.DIST_DIR / "downloads"
        dl_dir.mkdir(parents=True, exist_ok=True)
        for csv_file in sorted(anki_dir.glob("*.csv")):
            shutil.copy2(csv_file, dl_dir / csv_file.name)

    # --- sitemap（noindexページは除外） / RSS / robots / _headers ---
    # 更新日が分かるコンテンツだけ lastmod を付ける
    lastmod = {blog_tpl.article_url(a): a["date"] for a in articles}
    lastmod.update({reading_articles_tpl.article_url(a): a["date"] for a in reading_articles})
    urls = "\n".join(
        f"  <url><loc>{cfg['base_url']}{path}</loc>"
        + (f"<lastmod>{lastmod[path]}</lastmod>" if path in lastmod else "")
        + "</url>"
        for path in sorted(indexable))
    write_page("sitemap.xml",
               '<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               f"{urls}\n</urlset>\n")
    write_page("feed.xml", build_feed(cfg, articles))
    write_page("robots.txt",
               f"User-agent: *\nAllow: /\n\nSitemap: {cfg['base_url']}/sitemap.xml\n")
    write_page("_headers", """/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: SAMEORIGIN

/static/*
  Cache-Control: public, max-age=86400

/downloads/*
  X-Robots-Tag: noindex
  Content-Type: text/csv; charset=utf-8
  Content-Disposition: attachment
""")

    return pages


HREF_RE = re.compile(r'(?:href|src)="(/[^"]*)"')


def check_links(pages):
    """生成ページ内の内部リンクが実在するか検査する。"""
    broken = []
    for path, html in pages.items():
        for link in set(HREF_RE.findall(html)):
            link = link.split("#")[0].split("?")[0]
            if not link:
                continue
            if link in pages:
                continue
            target = config.DIST_DIR / link.lstrip("/")
            if link.endswith("/"):
                target = target / "index.html"
            if not target.is_file():
                broken.append(f"{path} -> {link}")
    return broken


def main():
    cfg = config.load_config()
    pages = build(cfg)
    broken = check_links(pages)
    print(f"generated {len(pages) + 1} pages -> {config.DIST_DIR}")  # +1 = 404.html
    if broken:
        print("BROKEN LINKS:")
        for b in sorted(broken):
            print(" ", b)
        sys.exit(1)
    print("link check: OK")


if __name__ == "__main__":
    main()
