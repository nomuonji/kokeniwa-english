"""静的サイトビルダー。data/ と content/ から dist/ に全ページを生成する。

使い方:
    python site/build_site.py
確認:
    cd dist && python -m http.server 8000
"""
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import config, data_loader, md
from lib.render import write_page
from templates import blog as blog_tpl
from templates import pages as pages_tpl
from templates import reading as reading_tpl
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
            "description": meta.get("description", ""),
            "html": html,
        })
    articles.sort(key=lambda a: a["date"], reverse=True)
    return articles


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

    # --- 読解問題 ---
    emit("/reading/", reading_tpl.render_index(cfg, problems))
    for d in config.DIFFICULTY_LEVELS:
        emit(f"/reading/level/{config.DIFFICULTY_LEVELS[d]['slug']}/",
             reading_tpl.render_level(cfg, problems, d))
    for category in {p["category"] for p in problems}:
        emit(reading_tpl.category_url(category),
             reading_tpl.render_category(cfg, problems, category))
    for i, p in enumerate(problems):
        emit(reading_tpl.problem_url(p), reading_tpl.render_problem(cfg, problems, i))

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

    # --- ブログ ---
    emit("/blog/", blog_tpl.render_index(cfg, articles))
    for a in articles:
        emit(blog_tpl.article_url(a), blog_tpl.render_article(cfg, a))

    # --- 固定ページ ---
    emit("/", pages_tpl.render_home(
        cfg, reading_count=len(problems), uscpa_count=counts["uscpa"],
        legal_count=counts["legal"], training_count=sum(training_counts.values()),
        articles=articles))
    emit("/sns/", pages_tpl.render_sns(cfg))
    emit("/books/", pages_tpl.render_books(cfg))
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

    # --- sitemap（noindexページは除外） / robots / _headers ---
    urls = "\n".join(
        f"  <url><loc>{cfg['base_url']}{path}</loc></url>"
        for path in sorted(indexable))
    write_page("sitemap.xml",
               '<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               f"{urls}\n</urlset>\n")
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
